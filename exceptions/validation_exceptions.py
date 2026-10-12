from pyexpat.errors import messages

from exceptions.currency_exchange_error import CurrencyExchangeError
from decimal import Decimal

"""Содержит пользовательские исключения, связанные с ошибками валидации данных. 
   Используются моделями и другими компонентами приложения для сигнализации о некорректных входных значениях.
   Обрабатываются на уровне HTTP-обработчика, где преобразуются в соответствующие ответы клиенту."""


class InvalidRateError(CurrencyExchangeError):
    def __init__(self, invalid_rate: Decimal | str) -> None:
        self.invalid_rate = invalid_rate
        message = f"Недопустимое значение параметра rate:{self.invalid_rate}"
        super().__init__(message)

class InvalidAmountError(CurrencyExchangeError):
    def __init__(self, invalid_amount: Decimal | str) -> None:
        self.invalid_amount = invalid_amount
        message = f"Недопустимое значение параметра amount:{self.invalid_amount}"
        super().__init__(message)

class InvalidCodeError(CurrencyExchangeError):
    def __init__(self, invalid_code: str):
        self.invalid_code = invalid_code
        message = f"Невалидное Значение кода {self.invalid_code}"
        super().__init__(message)

class InvalidSignError(CurrencyExchangeError):
    def __init__(self, invalid_sign: str) -> None:
        self.invalid_sign = invalid_sign
        message = f"Недопустимое значение параметра sign:{self.invalid_sign}"
        super().__init__(message)

class ImmutableAttributeError(CurrencyExchangeError):
    def __init__(self) -> None:
        message = "Недопустимая операция: аттрибут ID является неизменяемым"
        super().__init__(message)

class InvalidNameError(CurrencyExchangeError):
    def __init__(self, invalid_name: str) -> None:
        self.invalid_name = invalid_name
        message = f"Недопустимое значение параметра name:{self.invalid_name}"
        super().__init__(message)

