from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from model.currency import Currency

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from exceptions.validation_exceptions import InvalidRateError, ImmutableAttributeError


class ExchangeRate:
    """Класс предметной области, представляющий обменный курс между двумя валютами.
       Используется для хранения данных и их последующей передачи в HTTP-ответе."""
    def __init__(self, base_currency: Currency, target_currency: Currency, rate: str | float, ID: int | None =None) -> None:
        self._id = ID
        self.base_currency = base_currency
        self.target_currency = target_currency
        self.rate = rate

    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, ID: int) -> None:
        if self._id is None:
            self._id = ID
        else:
            raise ImmutableAttributeError

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
    def rate(self, new_rate: str | float) -> None:
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


    def to_dict(self) -> dict:
            return {
                "id": self.id,
                "baseCurrency": self.base_currency.to_dict(),
                "targetCurrency": self.target_currency.to_dict(),
                "rate": self.rate
            }