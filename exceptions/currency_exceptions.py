from exceptions.currency_exchange_error import CurrencyExchangeError

"""Классы исключения, описывающие ошибки при работе с валютами. 
Используются контроллером для передачи бизнес-ошибок обработчику HTTP-запросов."""

class CurrencyAlreadyExistsError(CurrencyExchangeError):
    pass


class CurrencyNotFoundError(CurrencyExchangeError):
    pass