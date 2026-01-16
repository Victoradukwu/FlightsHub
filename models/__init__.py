from .authentication import User, UserOut  # noqa: F401
from .common import AirlineAdminLink, TimestampMixin  # noqa: F401
from .flights import Airline, AirlineOut, Airport  # noqa: F401

AirlineOut.model_rebuild()
UserOut.model_rebuild()
