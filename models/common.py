from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, MetaData, Relationship, SQLModel

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

def utcnow():
    """Returns the current time in UTC."""
    return datetime.now(timezone.utc)


# Apply the convention to your metadata
SQLModel.metadata = MetaData(naming_convention=convention)

class TimestampMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": utcnow},
    )

class AdminStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class AirlineAdminLink(TimestampMixin, table=True):
    user_id: int | None = Field(foreign_key="users.id", primary_key=True)
    airline_id: int | None = Field(foreign_key="airline.id", primary_key=True)
    status: AdminStatus = Field(
        default=AdminStatus.ACTIVE, sa_column=Column(SAEnum(AdminStatus, name="admin_status"), nullable=False)
    )
    user: "User" = Relationship(back_populates="airline_links")  # pyright: ignore[reportUndefinedVariable] # noqa: F821
    airline: "Airline" = Relationship(back_populates="admin_links")  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
