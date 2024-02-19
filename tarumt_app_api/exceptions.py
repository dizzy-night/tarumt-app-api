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


class InvalidIP(AttendanceError):
    pass


class DuplicatedAttendance(AttendanceError):
    pass


class InvalidCode(AttendanceError):
    pass
