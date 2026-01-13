from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, field_validator
from pydantic_extra_types.timezone_name import TimeZoneName, timezone_name_settings
from sqlmodel import Field, SQLModel

from common.models import TimestampMixin


@timezone_name_settings(strict=False)
class TZNonStrict(TimeZoneName):
    pass


class AirportBase(SQLModel):
    airport_name: str = Field(unique=True, index=True)
    city: str
    iata_code: str = Field(unique=True, index=True)
    time_zone: TZNonStrict

    @property
    def full_name(self) -> str:
        return f"{self.airport_name}-{self.iata_code}"

    @field_validator("iata_code")
    def must_have_exactly_three_uppercase_letters(cls, v: str) -> str:
        """
        Validates that the input string contains exactly three uppercase letters.
        """
        if not (len(v) == 3 and v.isalpha() and v.isupper()):
            raise ValueError("Field must contain exactly three uppercase letters")
        return v


class AirportUpdate(BaseModel):
    airport_name: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    iata_code: Optional[str] = Field(default=None)
    time_zone: Optional[TZNonStrict] = Field(default=None)


class Airport(AirportBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
