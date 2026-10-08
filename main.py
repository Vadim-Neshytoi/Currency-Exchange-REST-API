from server.application_server import ApplicationServer
from handler.simple_handler import SimpleHandler
from controller.currency_controller import CurrencyController
from controller.exchange_rate_controller import ExchangeRateController
from database.database_manager import DatabaseManager
import logging
from settings import Settings

"""Точка входа в приложение. Выполняет инициализацию компонентов проекта и запускает HTTP-сервер."""


def create_application(settings: Settings):
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.log_path.parent.mkdir(parents=True, exist_ok=True)
    SimpleHandler.security_config = settings.security
    database_manager = DatabaseManager(db_path=settings.db_path)
    database_manager.connect()
    database_manager.initialize_tables()

    server_address = (settings.host, settings.port)
    httpd = ApplicationServer(server_address, SimpleHandler)

    httpd.database_manager = database_manager
    httpd.currency_controller = CurrencyController(database_manager)
    httpd.exchange_rate_controller = ExchangeRateController(database_manager)

    return httpd

def main():
    settings = Settings.load_from_env()
    logging.basicConfig(
        filename=settings.log_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        encoding='utf-8')
    application = create_application(settings)
    logging.info(f"Currency Exchange API started on port {settings.port}")


    try:
        application.serve_forever()
    except KeyboardInterrupt:
        print("Closing server")
    finally:
        application.server_close()
        application.database_manager.close_connection()


if __name__ == "__main__":
    main()




