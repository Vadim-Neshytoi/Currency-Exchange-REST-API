from exceptions.currency_exchange_error import CurrencyExchangeError

"""Содержит пользовательские исключения, связанные с ошибками валидации данных. 
   Используются моделями и другими компонентами приложения для сигнализации о некорректных входных значениях.
   Обрабатываются на уровне HTTP-обработчика, где преобразуются в соответствующие ответы клиенту."""


class InvalidRateError(CurrencyExchangeError):
    pass

class InvalidAmountError(CurrencyExchangeError):
    pass

class InvalidCodeError(CurrencyExchangeError):
    pass

class InvalidSignError(CurrencyExchangeError):
    pass

class ImmutableAttributeError(CurrencyExchangeError):
    pass