from __future__ import annotations

from http.server import ThreadingHTTPServer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database.database_manager import DatabaseManager
    from controller.currency_controller import CurrencyController
    from controller.exchange_rate_controller import ExchangeRateController


class ApplicationServer(ThreadingHTTPServer):
    database_manager: DatabaseManager
    currency_controller: CurrencyController
    exchange_rate_controller: ExchangeRateController