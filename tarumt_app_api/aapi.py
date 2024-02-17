from .api import BaseTarAppApi, require_login

from typing import Sequence
from .exceptions import *
from .typing.api_response import *


class TarAppAPI(BaseTarAppApi):

    def login(self, student_id: str, password: str):
        """
        :param student_id: The student's id
        :type student_id: str
        
        :param password: The student's password
        :type password: str

        :raises LoginError: 
        """
        ret = self._login(student_id, password)  # noqa: Unexpected argument?
        match ret.json():
            case {
                "msg": "failed",
                "msgdesc": reason
            }:
                raise LoginError(reason)
            case {
                "msg": "success",
                "token": token
            }:
                self.session.headers["X-Auth"] = token

    @require_login
    def book_facility(
            self,
            facility_id: str,
            booking_date: str,
            starting_time: str,
            ending_time: str,
            venue_id: str,
            students_id_and_name: Sequence[tuple[str, str]]
    ):
        """
        :param facility_id: The id of the facility. `facility_id` retrieved from :func:`fetch_facilities`
        :type facility_id: str

        :param booking_date: The date of the booking. Format in "DD/MM/YYYY"
        :type booking_date: str

        :param starting_time: The starting time of the booking. Format in "mm:ss"
        :type starting_time: str

        :param ending_time: The ending time of the booking. Format in "mm:ss"
        :type ending_time: str

        :param venue_id: The venue id of the facility. `venue_id` retrieved from :func:`fetch_facilities_venue`
        :type venue_id: str

        :param students_id_and_name: A sequence of tuple (of length 2) containing the student id and names.
        :type students_id_and_name: Sequence[tuple[str, str]]

        :raises FacilityBookingError: When the booking failed.
        """
        ret = self._book_facility(
            facility_id,
            booking_date,          # noqa
            starting_time,         # noqa
            ending_time,           # noqa
            venue_id,              # noqa
            students_id_and_name   # noqa
        )

        match ret.json():
            case {
                "msg": "failed",
                "msgdesc": reason
            }:
                raise FacilityBookingError(reason)

    @require_login
    def validate_student(self, student_id: str, student_name: str) -> bool:
        """

        :param student_id:

        :param student_name:

        :return:
        """
        ret = self._validate_student(student_id, student_name)  # noqa

        if ret.json()["msg"] == "success":
            return True
        return False

    @require_login
    def take_attendance(self, attendance_code: str):
        """

        :param attendance_code:

        :return:
        """
        ret = self._take_attendance(attendance_code)

        match ret.json():
            case {
                "msg": "taruc-ip",
                "msgdesc": reason
            }:
                raise AttendanceError(reason)

