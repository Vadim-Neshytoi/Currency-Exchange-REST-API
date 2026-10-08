from exceptions.validation_exceptions import InvalidCodeError, InvalidSignError, ImmutableAttributeError, \
    InvalidNameError
import re


class Currency:
    """Класс предметной области, представляющий валюту.
       Используется для хранения данных и их последующей передачи в HTTP-ответе."""

    CODE_PATTERN = re.compile(r"^[A-Z]{3}$")

    def __init__(self, code: str, name: str, sign: str, ID: int | None = None)->None:
        self._id = ID
        self.code = code
        self.name = name
        self.sign = sign

    @classmethod
    def normalize_code(cls, code: str) -> str:
        normalized = code.upper()
        if not cls.CODE_PATTERN.fullmatch(normalized):
            raise InvalidCodeError(code)
        return normalized

    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, ID: int) -> None:
        if self._id is None:
            self._id = ID
        else:
            raise ImmutableAttributeError()

    @property
    def code(self) -> str:
        return self._code

    @code.setter
    def code(self, code: str) -> None:
        normalized_code = self.normalized_code(code)
        self._code = normalized_code

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        if name.strip() == "":
            raise InvalidNameError()
        self._name = name


    @property
    def sign(self) -> str:
        return self._sign

    @sign.setter
    def sign(self, sign: str) -> None:
        if sign.strip() == "" or len(sign) > 3:
            raise InvalidSignError()
        self._sign = sign


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "sign": self.sign
        }











