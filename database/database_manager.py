from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path

import threading
import sqlite3
from decimal import Decimal
from model.currency import Currency
from model.exchange_rate import ExchangeRate

sqlite3.register_adapter(Decimal, lambda d: str(d))



class DatabaseManager:
    """Отвечает за взаимодействие с базой данных SQLite и инкапсулирует всю работу с SQL-запросами.
       Является промежуточным звеном между контроллерами и базой данных."""
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = db_path
        self._local = threading.local()

    def connect(self) -> None:
        connection = sqlite3.connect(self._db_path, timeout=5)
        connection.execute("PRAGMA foreign_keys = ON;")
        self._local.connection = connection
        self._local.cursor = connection.cursor()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "connection"):
            connection = sqlite3.connect(self._db_path, timeout=5)
            connection.execute("PRAGMA foreign_keys = ON;")
            self._local.connection = connection
        return self._local.connection

    def _get_cursor(self) -> sqlite3.Cursor:
        if not hasattr(self._local, "cursor"):
            self._local.cursor = self._get_connection().cursor()
        return self._local.cursor

    def _get_lastrowid(self) -> int:
        return self._get_cursor().lastrowid

    def execute_query(self, query: str, params: tuple = ()) -> list:
        connection = self._get_connection()
        cursor = self._get_cursor()
        try:
            cursor.execute(query, params)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        return cursor.fetchall()

    def close_connection(self) -> None:
        cursor = getattr(self._local, "cursor", None)
        connection = getattr(self._local, "connection", None)
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        if hasattr(self._local, "cursor"):
            del self._local.cursor
        if hasattr(self._local, "connection"):
            del self._local.connection

    def initialize_tables(self) -> None:
        self.execute_query("""CREATE TABLE IF NOT EXISTS currencies (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              code TEXT NOT NULL UNIQUE,
                              name TEXT NOT NULL,
                              sign TEXT NOT NULL)""")
        self.execute_query("""CREATE TABLE IF NOT EXISTS exchange_rates (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              base_currency_id INTEGER NOT NULL,
                              target_currency_id INTEGER NOT NULL,
                              rate REAL NOT NULL,
                              FOREIGN KEY (base_currency_id) REFERENCES currencies (id),
                              FOREIGN KEY (target_currency_id) REFERENCES currencies (id),
                              UNIQUE (base_currency_id, target_currency_id))""")

    @staticmethod
    def create_currency_from_row(currency_param: tuple[int, str, str, str]) -> Currency:
        db_id, db_code, db_name, db_sign = currency_param
        return Currency(code=db_code, name=db_name, sign=db_sign, ID=db_id)

    def insert_currency(self, currency_obj: Currency) -> Currency:
        query = "INSERT INTO currencies (code, name, sign) VALUES (?, ?, ?)"
        self.execute_query(query, (currency_obj.code, currency_obj.name, currency_obj.sign))
        generated_id = self._get_lastrowid()
        currency_obj.id = generated_id
        return currency_obj

    def find_currency_by_code(self, code_to_find: str) -> Currency | None:
        query = "SELECT * FROM currencies WHERE code = ?"
        currency = self.execute_query(query, (code_to_find,))
        if not currency:
            return None
        return self.create_currency_from_row(currency[0])

    def find_currency_by_id(self, db_id: int) -> Currency | None:
        query = "SELECT * FROM currencies WHERE id = ?"
        currency = self.execute_query(query, (db_id,))
        if not currency:
            return None
        return self.create_currency_from_row(currency[0])

    def find_all_currencies(self) -> list[Currency]:
        query = "SELECT * FROM currencies"
        rows = self.execute_query(query)
        currency_objects = []
        for currency_row in rows:
            currency_object = self.create_currency_from_row(currency_row)
            currency_objects.append(currency_object)
        return currency_objects

    def insert_exchange_rate(self, exchange_rate_obj: ExchangeRate) -> ExchangeRate:
        base_currency_id = exchange_rate_obj.base_currency.id
        target_currency_id = exchange_rate_obj.target_currency.id
        query = "INSERT INTO exchange_rates (base_currency_id, target_currency_id, rate) VALUES (?, ?, ?)"
        self.execute_query(query, (base_currency_id, target_currency_id, exchange_rate_obj.rate))
        generated_id = self._get_lastrowid()
        exchange_rate_obj.id = generated_id
        return exchange_rate_obj

    def find_exchange_rate(self, code_to_find_1: str, code_to_find_2: str) -> ExchangeRate | None:
        base_currency = self.find_currency_by_code(code_to_find_1)
        target_currency = self.find_currency_by_code(code_to_find_2)
        if not base_currency or not target_currency:
            return None
        query = "SELECT * FROM exchange_rates WHERE base_currency_id = ? and target_currency_id = ?"
        exchange_rate = self.execute_query(query, (base_currency.id, target_currency.id))
        if not exchange_rate:
            return None
        exchange_rate_param = exchange_rate[0]
        exchange_id, *_, rate = exchange_rate_param
        return ExchangeRate(base_currency=base_currency, target_currency=target_currency, rate=rate, ID=exchange_id)

    def find_all_exchange_rates(self) -> list[ExchangeRate]:
        query = "SELECT * FROM exchange_rates"
        rows = self.execute_query(query)
        exchange_rate_objects = []
        for exchange_rate_row in rows:
            db_id, db_base_currency, db_target_currency, db_rate = exchange_rate_row
            base_currency_obj = self.find_currency_by_id(db_base_currency)
            target_currency_obj = self.find_currency_by_id(db_target_currency)
            exchange_rate_object = ExchangeRate(base_currency=base_currency_obj, target_currency=target_currency_obj,
                                                rate=db_rate, ID=db_id )
            exchange_rate_objects.append(exchange_rate_object)
        return exchange_rate_objects

    def update_exchange_rate(self, exchange_rate_obj: ExchangeRate) -> ExchangeRate:
        base_currency_id = exchange_rate_obj.base_currency.id
        target_currency_id = exchange_rate_obj.target_currency.id
        rate = exchange_rate_obj.rate
        query = "UPDATE exchange_rates SET rate = ? WHERE base_currency_id = ? AND target_currency_id = ?"
        self.execute_query(query, (rate, base_currency_id, target_currency_id))
        return exchange_rate_obj



























