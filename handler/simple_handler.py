import simplejson as json
from typing import cast, NoReturn, Callable

from exceptions.currency_exchange_error import CurrencyExchangeError
from server.application_server import ApplicationServer
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging
from exceptions.currency_exceptions import CurrencyNotFoundError, CurrencyAlreadyExistsError
from exceptions.exchange_rate_exceptions import ExchangeRateNotFoundError, ExchangeRateAlreadyExistsError, \
    CrossCurrencyOverlapError, SameCurrencyExchangeRateError
from exceptions.validation_exceptions import InvalidAmountError, InvalidRateError, InvalidCodeError, InvalidSignError, \
    InvalidNameError, ImmutableAttributeError
from settings import AppSecurityConfig


class HttpError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message

RouteHandler = Callable[[], None]

ERROR_MAP = {
CurrencyNotFoundError: 404,
CurrencyAlreadyExistsError: 409,
ExchangeRateNotFoundError: 404,
ExchangeRateAlreadyExistsError: 409,
CrossCurrencyOverlapError: 400,
SameCurrencyExchangeRateError: 400,
InvalidAmountError: 400,
InvalidRateError: 400,
InvalidCodeError: 400,
InvalidSignError: 400,
InvalidNameError: 400,
ImmutableAttributeError: 400
}


class SimpleHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов, который занимается исключительно HTTP-уровнем
       (парсинг запросов, получение параметров, сериализация JSON, преобразование исключений в HTTP-коды)"""

    security_config: AppSecurityConfig

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def finish(self) -> None:
        try:
            super().finish()
        finally:
            server = self.app_server
            server.database_manager.close_connection()

    @property
    def app_server(self) -> ApplicationServer:
        return cast(ApplicationServer, self.server)

    def do_GET(self) -> None:
        self._dispatch(self._route_get)

    def do_POST(self) -> None:
        if not self._verify_body_size():
            return
        self._dispatch(self._route_post)

    def do_PATCH(self) -> None:
        if not self._verify_body_size():
            return
        self._dispatch(self._route_patch)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _dispatch(self, router: RouteHandler) -> None:
        try:
            router()
        except HttpError as http_error:
            self._send_json_response(http_error.status_code, {"message":http_error.message})
        except CurrencyExchangeError as error:
            error_type = type(error)
            if error_type not in ERROR_MAP:
                logging.critical(f"Ощибка конфигурации: {error_type.__name__} нет в ERROR_MAP")
                self._send_json_response(500, {"message": "Внутренняя ошибка сервера"})
                return
            status_code = ERROR_MAP[error_type]
            message = str(error)
            self._send_json_response(status_code, {"message": message})
        except Exception:
            logging.exception("Произошла непредвиденная ошибка")
            self._send_json_response(500, {"message": "Ошибка сервера"})

    def _route_get(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        if path == "/":
            self._handle_index()
        elif path == "/currencies":
            self._handle_get_currencies()
        elif path.startswith("/currency/"):
            self._handle_get_currency(path)
        elif path == "/exchangeRates":
            self._handle_get_exchange_rates()
        elif path.startswith("/exchangeRate/"):
            self._handle_get_exchange_rate(path)
        elif path == "/exchange":
            self._handle_get_exchange(query_params)
        else:
            self._raise_http_error(404, "Неверный запрос")

    def _route_post(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/currencies":
            self._handle_post_currencies()
        elif path == "/exchangeRates":
            self._handle_post_exchange_rates()
        else:
            self._raise_http_error(404, "Неверный запрос")

    def _route_patch(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path.startswith("/exchangeRate/"):
            self._handle_patch_exchange_rate(path)
        else:
            self._raise_http_error(404, "Неверный запрос")

    # Обработчики GET метода

    def _handle_index(self) -> None:
        self._send_json_response(200, {"message": "Главная страница"})

    def _handle_get_currencies(self) -> None:
        currencies = self.app_server.currency_controller.get_all_currencies()
        currencies_list = []
        for currency in currencies:
            currencies_list.append(currency.to_dict())
        self._send_json_response(200, currencies_list)

    def _handle_get_currency(self, path: str) -> None:
        currency_code = path[len("/currency/"):].strip()
        if not currency_code:
            self._raise_http_error(400, "Неверный запрос")
        currency = self.app_server.currency_controller.get_currency_by_code(currency_code)
        currency_dict = currency.to_dict()
        self._send_json_response(200, currency_dict)

    def _handle_get_exchange_rates(self) -> None:
        exchange_rates = self.app_server.exchange_rate_controller.get_all_exchange_rates()
        exchange_rates_list = []
        for exchange_rate in exchange_rates:
            exchange_rates_list.append(exchange_rate.to_dict())
        self._send_json_response(200, exchange_rates_list)

    def _handle_get_exchange_rate(self, path: str) -> None:
        currency_pair = path[len("/exchangeRate/"):].strip()
        if not currency_pair:
            self._raise_http_error(400, "Неверный запрос")
        base_currency_code = currency_pair[:3]
        target_currency_code = currency_pair[3:]
        if not base_currency_code or not target_currency_code:
            self._raise_http_error(400, "Один из кодов валют в паре не указан")
        exchange_rate = self.app_server.exchange_rate_controller.get_exchange_rate_by_codes(base_currency_code,
                                                                                            target_currency_code)
        exchange_rate_dict = exchange_rate.to_dict()
        self._send_json_response(200, exchange_rate_dict)

    def _handle_get_exchange(self, query_params: dict[str, list[str]]) -> None:
        required_fields = ["from", "to", "amount"]
        missing_fields = self._find_missing_fields(query_params, required_fields)
        if missing_fields:
            self._raise_http_error(400, f"Пропущены обязательные параметры: {", ".join(missing_fields)}")
        currency_pair_from = query_params['from'][0]
        currency_pair_to = query_params['to'][0]
        exchange_result_obj = self.app_server.exchange_rate_controller.exchange(base_currency_code=currency_pair_from,
                                                                                target_currency_code=currency_pair_to,
                                                                                amount=query_params["amount"][0])
        exchange_dict = exchange_result_obj.to_dict()
        self._send_json_response(200, exchange_dict)

    # Обработчики POST метода

    def _handle_post_currencies(self) -> None:
        params = self._read_form_data()
        required_fields = ["name", "code", "sign"]
        missing_fields = self._find_missing_fields(params, required_fields)
        if missing_fields:
            self._raise_http_error(400, f"Пропущены обязательные параметры: {", ".join(missing_fields)}")
        created_currency = self.app_server.currency_controller.create_currency(code=params["code"][0],
                                                                               name=params["name"][0],
                                                                               sign=params["sign"][0])
        currency_dict = created_currency.to_dict()
        self._send_json_response(201, currency_dict)

    def _handle_post_exchange_rates(self) -> None:
        params = self._read_form_data()
        required_fields = ["baseCurrencyCode", "targetCurrencyCode", "rate"]
        missing_fields = self._find_missing_fields(params, required_fields)
        if missing_fields:
            self._raise_http_error(400, f"Пропущены обязательные параметры: {", ".join(missing_fields)}")
        created_exchange_rate = self.app_server.exchange_rate_controller.create_exchange_rate(code_1=params["baseCurrencyCode"][0],
                                                                                              code_2=params["targetCurrencyCode"][0],
                                                                                              rate=params["rate"][0])
        exchange_rate_dict = created_exchange_rate.to_dict()
        self._send_json_response(201, exchange_rate_dict)

    # Обработчики PATCH метода

    def _handle_patch_exchange_rate(self, path: str) -> None:
        params = self._read_form_data()
        required_fields = ["rate"]
        missing_fields = self._find_missing_fields(params, required_fields)
        if missing_fields:
            self._raise_http_error(400, f"Пропущен обязательный параметр: {", ".join(missing_fields)}")
        currency_pair = path[len("/exchangeRate/"):]
        base_currency_code = currency_pair[:3]
        target_currency_code = currency_pair[3:]
        new_rate = params["rate"][0]
        exchange_rate_obj = self.app_server.exchange_rate_controller.update_exchange_rate(base_currency_code,
                                                                                          target_currency_code,
                                                                                          new_rate)
        exchange_rate_obj_to_dict = exchange_rate_obj.to_dict()
        self._send_json_response(200, exchange_rate_obj_to_dict)

    def _read_form_data(self) -> dict[str, list[str]]:
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        params = parse_qs(post_data.decode("utf-8"))
        return params

    def _raise_http_error(self, status_code: int, message: str) -> NoReturn:
        raise HttpError(status_code, message)

    def _send_json_response(self, status_code: int, data: dict | list) -> None:
        self.send_response(status_code)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, use_decimal=True).encode("utf-8"))

    def _verify_body_size(self) -> bool:
        content_length_str = self.headers.get('Content-Length')
        if not content_length_str:
            data = {"message": "Missing Content-Length header."}
            self._send_json_response(411, data)
            return False
        try:
            content_length = int(content_length_str)
        except ValueError:
            data = {"message": "Invalid Content-Length header."}
            self._send_json_response(400, data)
            return False
        if content_length < 0:
            data = {"message": "Invalid Content-Length header."}
            self._send_json_response(400, data)
            return False
        if content_length > self.security_config.max_body_size:
            data = {"message": "Request body is too large."}
            self._send_json_response(413, data)
            return False
        return True

    def _send_cors_headers(self) -> None:
        client_origin = self.headers.get('Origin')
        if client_origin in self.security_config.cors_allowed_origins:
            self.send_header('Access-Control-Allow-Origin', client_origin)
        else:
            pass
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    @staticmethod
    def _find_missing_fields(params: dict[str, list[str]], required_fields: list[str]) -> list[str]:
        missing_fields = []
        for field in required_fields:
            values = params.get(field)
            if not values or not values[0].strip():
                missing_fields.append(field)
        return missing_fields
