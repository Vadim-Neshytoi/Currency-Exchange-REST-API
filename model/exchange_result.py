from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from model.currency import Currency

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from exceptions.validation_exceptions import InvalidAmountError, InvalidRateError


class ExchangeResult:
    """Класс предметной области, содержащий результат операции обмена валют.
       Используется для формирования ответа эндпоинта обмена."""
    def __init__(self, base_currency: Currency, target_currency: Currency, rate: Decimal, amount: str) -> None:
        self.base_currency = base_currency
        self.target_currency = target_currency
        self.rate = rate
        self.amount = amount
        self._converted_amount = (self.amount * self.rate).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)

    @property
    def base_currency(self) -> Currency:
        return self._base_currency

    @base_currency.setter
    def base_currency(self, base_currency: Currency) -> None:
        self._base_currency = base_currency

    @property
    def target_currency(self) -> Currency:
        return self._target_currency

    @target_currency.setter
    def target_currency(self, target_currency: Currency) -> None:
        self._target_currency = target_currency

    @property
    def rate(self) -> Decimal:
        return self._rate

    @rate.setter
    def rate(self, new_rate: Decimal) -> None:
        try:
            text_new_rate = str(new_rate)
            if text_new_rate.startswith('+'):
                raise InvalidRateError()
            decimal_rate = Decimal(text_new_rate)
            if decimal_rate <= 0:
                raise InvalidRateError()
            self._rate = decimal_rate.quantize(Decimal("1.000000"), rounding=ROUND_HALF_UP)
        except InvalidOperation:
            raise InvalidRateError()

    @property
    def amount(self) -> Decimal:
        return self._amount

    @amount.setter
    def amount(self, amount: str | float) -> None:
        try:
            text_amount = str(amount)
            if text_amount.startswith('+'):
                raise InvalidAmountError()
            decimal_amount = Decimal(text_amount)
            if decimal_amount < 0:
                raise InvalidAmountError()
            self._amount = decimal_amount
        except InvalidOperation:
            raise InvalidAmountError()

    @property
    def converted_amount(self) -> Decimal:
        return self._converted_amount

    def to_dict(self) -> dict:
            return {
                "baseCurrency": self.base_currency.to_dict(),
                "targetCurrency": self.target_currency.to_dict(),
                "rate": self.rate,
                "amount": self.amount,
                "convertedAmount": self.converted_amount
            }












