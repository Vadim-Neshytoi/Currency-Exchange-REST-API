from exceptions.validation_exceptions import InvalidCodeError, InvalidSignError, ImmutableAttributeError
import re


class Currency:
    """Класс предметной области, представляющий валюту.
       Используется для хранения данных и их последующей передачи в HTTP-ответе."""
    def __init__(self, code: str, name: str, sign: str, ID: int | None = None)->None:
        self._id = ID
        self.code = code
        self.name = name
        self.sign = sign


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
    def code(self) -> str:
        return self._code

    @code.setter
    def code(self, code: str) -> None:
        if len(code) != 3 or not re.match(r"^[a-zA-Z]+$", code):
            raise InvalidCodeError()
        self._code = code.upper()

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name


    @property
    def sign(self) -> str:
        return self._sign

    @sign.setter
    def sign(self, sign: str) -> None:
        if len(sign) > 3:
            raise InvalidSignError()
        self._sign = sign


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "sign": self.sign
        }











