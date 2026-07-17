from http.server import HTTPServer
from handler.simple_handler import SimpleHandler
from controller.currency_controller import CurrencyController
from controller.exchange_rate_controller import ExchangeRateController
from database.database_manager import DatabaseManager
from pathlib import Path
import logging


"""Точка входа в приложение. Выполняет инициализацию компонентов проекта и запускает HTTP-сервер."""


server = ("", 8000)
httpd = HTTPServer(server, SimpleHandler)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "currency_exchange.db"
database_manager = DatabaseManager(db_path=DB_PATH)
database_manager.connect()
database_manager.initialize_tables()
httpd.currency_controller = CurrencyController(database_manager)
httpd.exchange_rate_controller = ExchangeRateController(database_manager)

logging.basicConfig(
                    filename='server_app.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    encoding='utf-8')
logging.info("Currency Exchange API started on port 8000")

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("Closing server")
finally:
    httpd.server_close()
    database_manager.close_connection()






