import simplejson as json
from typing import cast
from server.application_server import ApplicationServer
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging
from exceptions.currency_exceptions import CurrencyNotFoundError, CurrencyAlreadyExistsError
from exceptions.exchange_rate_exceptions import ExchangeRateNotFoundError, ExchangeRateAlreadyExistsError
from exceptions.validation_exceptions import InvalidAmountError, InvalidRateError, InvalidCodeError, InvalidSignError
from settings import AppSecurityConfig


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
            server = cast(ApplicationServer, self.server)
            server.database_manager.close_connection()

    def send_json_response(self, status_code: int, data: dict | list) -> None:
        self.send_response(status_code)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, use_decimal=True).encode("utf-8"))

    def _verify_body_size(self) -> bool:
        content_length_str = self.headers.get('Content-Length')
        if not content_length_str:
            data = {"message": "Missing Content-Length header."}
            self.send_json_response(411, data)
            return False
        try:
            content_length = int(content_length_str)
        except ValueError:
            data = {"message": "Invalid Content-Length header."}
            self.send_json_response(400, data)
            return False
        if content_length < 0:
            data = {"message": "Invalid Content-Length header."}
            self.send_json_response(400, data)
            return False
        if content_length > self.security_config.max_body_size:
            data = {"message": "Request body is too large."}
            self.send_json_response(413, data)
            return False
        return True

    def send_cors_headers(self) -> None:
        client_origin = self.headers.get('Origin')
        if client_origin in self.security_config.cors_allowed_origins:
            self.send_header('Access-Control-Allow-Origin', client_origin)
        else:
            pass
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')


    def do_GET(self) -> None:
        server = cast(ApplicationServer, self.server)
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            if path == "/":
                data = {"message": "Главная страница"}
                self.send_json_response(200, data)
            elif path == "/currencies":
                currencies = server.currency_controller.get_all_currencies()
                currencies_list = []
                for currency in currencies:
                    currency_dict = currency.to_dict()
                    currencies_list.append(currency_dict)
                self.send_json_response(200, currencies_list)

            elif path.startswith("/currency/"):
                currency_code = path[len("/currency/"):]
                if currency_code:
                    try:
                        currency = server.currency_controller.get_currency_by_code(currency_code)
                    except InvalidCodeError as e:
                        data = {"message": f"Невалидное Значение кода {e.invalid_code}"}
                        self.send_json_response(400, data)
                        return
                    except CurrencyNotFoundError:
                        data = {"message": f"Валюта '{currency_code}' не найдена"}
                        self.send_json_response(404, data)
                        return
                    currency_dict = currency.to_dict()
                    self.send_json_response(200, currency_dict)
                    return
                data = {"message": "Неверный запрос"}
                self.send_json_response(400, data)
            elif path == "/exchangeRates":
                exchange_rates = server.exchange_rate_controller.get_all_exchange_rates()
                exchange_rates_list = []
                for exchange_rate in exchange_rates:
                    exchange_rate_dict = exchange_rate.to_dict()
                    exchange_rates_list.append(exchange_rate_dict)
                self.send_json_response(200, exchange_rates_list)
            elif path.startswith("/exchangeRate/"):
                currency_pair = path[len("/exchangeRate/"):]
                base_currency_code = currency_pair[:3]
                target_currency_code = currency_pair[3:]
                try:
                    exchange_rate = server.exchange_rate_controller.get_exchange_rate_by_codes(base_currency_code,
                                                                                               target_currency_code)
                except InvalidCodeError as e:
                    data = {"message": f"Невалидное Значение кода {e.invalid_code}"}
                    self.send_json_response(400, data)
                    return
                except ExchangeRateNotFoundError:
                    data = {"message": f"Обменный курс {base_currency_code}/{target_currency_code} не найден"}
                    self.send_json_response(404, data)
                    return
                exchange_rate_dict = exchange_rate.to_dict()
                self.send_json_response(200, exchange_rate_dict)
            elif path == "/exchange":
                required_fields = ["from", "to", "amount"]
                missing_fields = self.find_missing_fields(query_params, required_fields)
                if not missing_fields:
                    currency_pair_from = query_params['from'][0]
                    currency_pair_to = query_params['to'][0]
                    try:
                        exchange_result_obj = server.exchange_rate_controller.exchange(base_currency_code=currency_pair_from,
                                                                             target_currency_code=currency_pair_to,
                                                                             amount=query_params["amount"][0])
                    except InvalidCodeError as e:
                        data = {"message": f"Невалидное Значение кода {e.invalid_code}"}
                        self.send_json_response(400, data)
                        return
                    except InvalidAmountError:
                        data = {"message": f"Недопустимое значение параметра amount:{query_params["amount"][0]}"}
                        self.send_json_response(400, data)
                        return
                    except CurrencyNotFoundError:
                        data = {"message": "Валюта не найдена"}
                        self.send_json_response(404, data)
                        return
                    except ExchangeRateNotFoundError:
                        data = {"message": "Курс не найден"}
                        self.send_json_response(404, data)
                        return
                    exchange_dict = exchange_result_obj.to_dict()
                    self.send_json_response(200, exchange_dict)
                    return
                else:
                    data = {"message": f"Пропущены обязательные параметры: {", ".join(missing_fields)}"}
                    self.send_json_response(400, data)
            else:
                data = {"message": "Страница не найдена"}
                self.send_json_response(404, data)
        except Exception:
            logging.exception(f"Произошла непредвиденная ошибка")
            data = {"message": "Ошибка сервера"}
            self.send_json_response(500, data)

    @staticmethod
    def find_missing_fields(params: dict[str, list[str]], required_fields: list[str]) -> list[str]:
        missing_fields = []
        for field in required_fields:
            values = params.get(field)
            if not values or not values[0].strip():
                missing_fields.append(field)
        return missing_fields


    def do_POST(self) -> None:
        if not self._verify_body_size():
            return
        server = cast(ApplicationServer, self.server)
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            if path == "/currencies":
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                params = parse_qs(post_data.decode("utf-8"))
                required_fields = ["name", "code", "sign"]
                missing_fields = self.find_missing_fields(params, required_fields)
                if not missing_fields:
                    try:
                        created_currency = server.currency_controller.create_currency(code=params["code"][0],
                                                                              name=params["name"][0],
                                                                              sign=params["sign"][0])
                    except InvalidCodeError as e:
                        data = {"message": f"Невалидное Значение кода {e.invalid_code}"}
                        self.send_json_response(400, data)
                        return
                    except InvalidSignError:
                        data = {"message": f"Недопустимое значение параметра sign:{params["sign"][0]}"}
                        self.send_json_response(400, data)
                        return
                    except CurrencyAlreadyExistsError:
                        data = {"message": "Такакя валюта уже есть"}
                        self.send_json_response(409, data)
                        return
                    currency_dict = created_currency.to_dict()
                    self.send_json_response(201, currency_dict)
                    return
                else:
                    data = {"message": f"Пропущены обязательные параметры: {", ".join(missing_fields)}"}
                    self.send_json_response(400, data)
            elif path == "/exchangeRates":
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                params = parse_qs(post_data.decode("utf-8"))
                required_fields = ["baseCurrencyCode", "targetCurrencyCode", "rate"]
                missing_fields = self.find_missing_fields(params, required_fields)
                if not missing_fields:
                    try:
                        created_exchange_rate = server.exchange_rate_controller.create_exchange_rate(code_1=params["baseCurrencyCode"][0],
                                                                                                      code_2=params["targetCurrencyCode"][0],
                                                                                                      rate=params["rate"][0])
                    except InvalidCodeError as e:
                        data = {"message": f"Невалидное Значение кода {e.invalid_code}"}
                        self.send_json_response(400, data)
                        return
                    except InvalidRateError:
                        data = {"message": f"Недопустимое значение параметра rate:{params["rate"][0]}"}
                        self.send_json_response(400, data)
                        return
                    except CurrencyNotFoundError:
                        data = {"message": "Валюта не найдена"}
                        self.send_json_response(404, data)
                        return
                    except ExchangeRateAlreadyExistsError:
                        data = {"message": "Такой курс уже существует"}
                        self.send_json_response(409, data)
                        return
                    exchange_rate_dict = created_exchange_rate.to_dict()
                    self.send_json_response(201, exchange_rate_dict)
                    return
                else:
                    data = {"message": f"Пропущены обязательные параметры: {", ".join(missing_fields)}"}
                    self.send_json_response(400, data)
            else:
                data = {"message": "Неверный запрос"}
                self.send_json_response(404, data)
        except Exception:
            logging.exception(f"Произошла непредвиденная ошибка")
            data = {"message": "Ошибка сервера"}
            self.send_json_response(500, data)

    def do_PATCH(self) -> None:
        if not self._verify_body_size():
            return
        server = cast(ApplicationServer, self.server)
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            if path.startswith("/exchangeRate/"):
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                params = parse_qs(post_data.decode("utf-8"))
                required_fields = ["rate"]
                missing_fields = self.find_missing_fields(params, required_fields)
                if not missing_fields:
                    currency_pair = path[len("/exchangeRate/"):]
                    base_currency_code = currency_pair[:3]
                    target_currency_code = currency_pair[3:]
                    new_rate = params.get("rate")[0]
                    try:
                        exchange_rate_obj = server.exchange_rate_controller.update_exchange_rate(base_currency_code,
                                                                                                 target_currency_code,
                                                                                                 new_rate)
                    except InvalidCodeError as e:
                        data = {"message": f"Невалидное Значение кода {e.invalid_code}"}
                        self.send_json_response(400, data)
                        return
                    except InvalidRateError:
                        data = {"message": f"Недопустимое значение параметра rate:{new_rate}"}
                        self.send_json_response(400, data)
                        return
                    except ExchangeRateNotFoundError:
                        data = {"message": f"Обменный курс {base_currency_code}/{target_currency_code} не найден"}
                        self.send_json_response(404, data)
                        return
                    exchange_rate_obj_to_dict = exchange_rate_obj.to_dict()
                    self.send_json_response(200, exchange_rate_obj_to_dict)
                else:
                    data = {"message": f"Пропущен обязательный параметр: {", ".join(missing_fields)}"}
                    self.send_json_response(400, data)
            else:
                data = {"message": "Неверный запрос"}
                self.send_json_response(404, data)
        except Exception:
            logging.exception(f"Произошла непредвиденная ошибка")
            data = {"message": "Ошибка сервера"}
            self.send_json_response(500, data)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()
