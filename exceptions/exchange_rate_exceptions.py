from exceptions.currency_exchange_error import CurrencyExchangeError

"""Классы исключения, описывающие ошибки при работе с обменными курсами. 
Используются контроллером для передачи бизнес-ошибок обработчику HTTP-запросов."""


class ExchangeRateAlreadyExistsError(CurrencyExchangeError):
    pass


class ExchangeRateNotFoundError(CurrencyExchangeError):
    pass
