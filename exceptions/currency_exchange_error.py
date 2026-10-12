class CurrencyExchangeError(Exception):
    """Базовый класс ошибок проекта"""
    def __init__(self, message):
        super().__init__(message)