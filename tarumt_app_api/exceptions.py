__all__ = (
    "LoginError",
    "FacilityBookingError",
    "NotLoggedIn",
    "InvalidSession",
    "AttendanceError"
)


class LoginError(Exception):
    pass


class FacilityBookingError(Exception):
    pass


class NotLoggedIn(Exception):
    pass


class InvalidSession(Exception):
    pass


class AttendanceError(Exception):
    pass
