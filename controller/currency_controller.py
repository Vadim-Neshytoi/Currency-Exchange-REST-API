from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from database.database_manager import DatabaseManager

from model.currency import Currency
from sqlite3 import IntegrityError
from exceptions.currency_exceptions import CurrencyAlreadyExistsError, CurrencyNotFoundError


class CurrencyController:
    """Класс реализует бизнес-логику приложения и является промежуточным звеном между HTTP-обработчиком и базой данных.
     Отвечает за работу с валютами."""
    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def get_currency_by_code(self, code_to_find: str) -> Currency:
        currency = self._database_manager.find_currency_by_code(code_to_find)
        if currency is None:
            raise CurrencyNotFoundError()
        return currency

    def get_all_currencies(self) -> list[Currency]:
        currencies = self._database_manager.find_all_currencies()
        return currencies

    def create_currency(self, code: str, name: str, sign: str) -> Currency:
        try:
            currency_obj = Currency(code=code, name=name, sign=sign)
            return self._database_manager.insert_currency(currency_obj)
        except IntegrityError:
            raise CurrencyAlreadyExistsError()










































