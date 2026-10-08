from exceptions.currency_exchange_error import CurrencyExchangeError

"""Содержит пользовательские исключения, связанные с ошибками валидации данных. 
   Используются моделями и другими компонентами приложения для сигнализации о некорректных входных значениях.
   Обрабатываются на уровне HTTP-обработчика, где преобразуются в соответствующие ответы клиенту."""


class InvalidRateError(CurrencyExchangeError):
    pass

class InvalidAmountError(CurrencyExchangeError):
    pass

class InvalidCodeError(CurrencyExchangeError):
    def __init__(self, invalid_code: str):
        self.invalid_code = invalid_code
        super().__init__(invalid_code)

class InvalidSignError(CurrencyExchangeError):
    pass

class ImmutableAttributeError(CurrencyExchangeError):
    pass

class InvalidNameError(CurrencyExchangeError):
    pass

