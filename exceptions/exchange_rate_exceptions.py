from exceptions.currency_exchange_error import CurrencyExchangeError

"""Классы исключения, описывающие ошибки при работе с обменными курсами. 
Используются контроллером для передачи бизнес-ошибок обработчику HTTP-запросов."""


class ExchangeRateAlreadyExistsError(CurrencyExchangeError):
    def __init__(self, currency_code_1: str, currency_code_2: str) -> None:
        self.currency_code_1 = currency_code_1
        self.currency_code_2 = currency_code_2
        message = f"Такой курс уже существует: {self.currency_code_1}/{self.currency_code_2}"
        super().__init__(message)

class ExchangeRateNotFoundError(CurrencyExchangeError):
    def __init__(self, currency_code_1: str, currency_code_2: str) -> None:
        self.currency_code_1 = currency_code_1
        self.currency_code_2 = currency_code_2
        message = f"Курс не найден: {self.currency_code_1}/{self.currency_code_2}"
        super().__init__(message)

class SameCurrencyExchangeRateError(CurrencyExchangeError):
    def __init__(self) -> None:
        message = "Базовая и целеваявалюта не могут совпадать"
        super().__init__(message)

class CrossCurrencyOverlapError(CurrencyExchangeError):
    def __init__(self) -> None:
        message = "Промежуточная валюта обмена не может совпадать с базовой или целевой валютой"
        super().__init__(message)
