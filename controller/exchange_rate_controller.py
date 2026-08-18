from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from database.database_manager import DatabaseManager

from model.exchange_rate import ExchangeRate
from model.exchange_result import ExchangeResult
from sqlite3 import IntegrityError
from exceptions.exchange_rate_exceptions import ExchangeRateAlreadyExistsError, ExchangeRateNotFoundError
from exceptions.currency_exceptions import CurrencyNotFoundError


class ExchangeRateController:
    """Класс реализует бизнес-логику приложения и является промежуточным звеном между HTTP-обработчиком и базой данных.
     Отвечает за работу с обменными курсами."""
    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def create_exchange_rate(self, code_1: str, code_2: str, rate: str) -> ExchangeRate:
        currency_obj_1 = self._database_manager.find_currency_by_code(code_1)
        currency_obj_2 = self._database_manager.find_currency_by_code(code_2)
        if currency_obj_1 is None or currency_obj_2 is None:
            raise CurrencyNotFoundError()
        exchange_rate_obj = ExchangeRate(base_currency=currency_obj_1, target_currency=currency_obj_2, rate=rate)
        try:
            return self._database_manager.insert_exchange_rate(exchange_rate_obj)
        except IntegrityError:
            raise ExchangeRateAlreadyExistsError()


    def get_exchange_rate_by_codes(self, code_1: str, code_2: str) -> ExchangeRate:
        exchange_rate_obj = self._database_manager.find_exchange_rate(code_1, code_2)
        if exchange_rate_obj is None:
            raise ExchangeRateNotFoundError()
        return exchange_rate_obj

    def get_all_exchange_rates(self) -> list[ExchangeRate]:
        exchange_rate_obj = self._database_manager.find_all_exchange_rates()
        return exchange_rate_obj

    def update_exchange_rate(self, code_1: str, code_2: str, new_rate: str) -> ExchangeRate:
        exchange_rate_obj = self._database_manager.find_exchange_rate(code_1, code_2)
        if exchange_rate_obj is None:
            raise ExchangeRateNotFoundError()
        exchange_rate_obj.rate = new_rate
        return self._database_manager.update_exchange_rate(exchange_rate_obj)


    def exchange(self, base_currency_code: str, target_currency_code: str, amount: str) -> ExchangeResult:
        ExchangeResult.validate_amount(amount)
        base_currency_obj = self._database_manager.find_currency_by_code(base_currency_code)
        target_currency_obj = self._database_manager.find_currency_by_code(target_currency_code)
        if base_currency_obj is None or target_currency_obj is None:
            raise CurrencyNotFoundError()
        direct_exchange_rate_obj = self._database_manager.find_exchange_rate(base_currency_code, target_currency_code)
        if direct_exchange_rate_obj:
            rate = direct_exchange_rate_obj.rate
            return ExchangeResult(base_currency=base_currency_obj, target_currency=target_currency_obj, rate=rate,
                              amount=amount)
        reverse_exchange_rate_obj = self._database_manager.find_exchange_rate(target_currency_code, base_currency_code)
        if reverse_exchange_rate_obj:
            reverse_rate = reverse_exchange_rate_obj.rate
            rate = 1 / reverse_rate
            return ExchangeResult(base_currency=base_currency_obj, target_currency=target_currency_obj, rate=rate,
                              amount=amount)
        usd_exchange_rate_obj_1 = self._database_manager.find_exchange_rate("USD", base_currency_code)
        usd_exchange_rate_obj_2 = self._database_manager.find_exchange_rate("USD", target_currency_code)
        if usd_exchange_rate_obj_1 and usd_exchange_rate_obj_2:
            rate_1 = usd_exchange_rate_obj_1.rate
            rate_2 = usd_exchange_rate_obj_2.rate
            rate = rate_2 / rate_1
            return ExchangeResult(base_currency=base_currency_obj, target_currency=target_currency_obj, rate=rate,
                              amount=amount)
        raise ExchangeRateNotFoundError()
































