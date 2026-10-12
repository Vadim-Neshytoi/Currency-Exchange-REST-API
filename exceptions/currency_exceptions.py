from exceptions.currency_exchange_error import CurrencyExchangeError

"""Классы исключения, описывающие ошибки при работе с валютами. 
Используются контроллером для передачи бизнес-ошибок обработчику HTTP-запросов."""

class CurrencyAlreadyExistsError(CurrencyExchangeError):
    def __init__(self, currency_code: str) -> None:
        self.currency_code = currency_code
        message = f"Ошибка: валюта с таким кодом: {self.currency_code} уже сущетвует"
        super().__init__(message)

class CurrencyNotFoundError(CurrencyExchangeError):
    def __init__(self, currency_code: str) -> None:
        self.currency_code = currency_code
        message = f"Валюта '{self.currency_code}' не найдена"
        super().__init__(message)
