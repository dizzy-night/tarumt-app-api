import requests
from typing import Sequence, Callable

from .exceptions import *
from .responses_annotation import *


APP_VERSION = "2.0.18"


class TarAppAPI:
    def __init__(self):
        self.session = requests.Session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def is_login(self) -> bool:
        return "X-Auth" in self.session.headers

    @staticmethod
    def require_login[T, **P](func: Callable[P, T]) -> Callable[P, T]:
        """Checks if header "X-Auth" is present in the headers"""

        def check(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if not self.is_login():
                raise NotLoggedIn()
            return func(self, *args, **kwargs)

        return check

    @staticmethod
    def check_session_valid[**P](func: Callable[P, requests.Response]) -> Callable[P, requests.Response]:
        """Checks if the response is a failed response."""
        def check(self, *args: P.args, **kwargs: P.kwargs) -> requests.Response:
            ret = func(self, *args, **kwargs)

            match ret.json():
                case {
                    "msg": "failed",
                    "msgdesc": reason,
                    "statusCd": "invalid-token"
                }:
                    raise InvalidSession(reason)

            return ret

        return check

    def login(self, student_id: str, password: str):
        """
        :param student_id: The student's id
        :type student_id: str
        
        :param password: The student's password
        :type password: str
        
        :raises LoginError: 
        """
        ret = self._login(student_id, password)

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
            booking_date,
            starting_time,
            ending_time,
            venue_id,
            students_id_and_name
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
        ret = self._validate_student(student_id, student_name)

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

    @check_session_valid
    def _login(self, student_id: str, password: str):
        """
        (on failure)
        {
          "msg": "failed",
          "msgdesc": "Invalid user id or password",
          "token": ""
        }
        (on success)
        {
          "msg": "success",
          "brncd": <campus identifier: str>,
          "fullname": <student name: str>,
          "msgdesc": "",
          "userid": <student id: str>,
          "email": <student education email address: str>,
          "token": <session token: str>
        }
        """
        payload = {
            "username": student_id,
            "password": password,
            "deviceid": "",
            "devicemodel": "",
            "appversion": APP_VERSION
        }
        return self.session.post("https://app.tarc.edu.my/MobileService/login.jsp", data=payload)

    @require_login
    @check_session_valid
    def _fetch_app_access(self) -> requests.Response:
        """
        {
          "msg": "success",
          "access": [
            "facility-booking"
          ],
          "msgdesc": ""
        }
        """
        params = {
            "act": "app-access"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXAppAccess.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_notice(self) -> requests.Response:
        """
        {
          "msg": "",
          "show": "N",
          "msgdesc": ""
        }
        """
        params = {
            "act": "get"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXStudentNotice.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_announcements_count(self) -> requests.Response:
        """
        {
          "msg": "success",
          "total": 5,
          "msgdesc": ""
        }
        """
        params = {
            "act": "get-new"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXStudentAnnouncement.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_announcements(self, page: int = 1, limit: int = 10, msg_type: str = "all") -> requests.Response:
        """
        {
          "msg": "",
          "list": [
            {
              "ftitle": <announcement title: str>,
              "fsender": <sender dept: str>,
              "ftype": "Announcement",
              "isread": <"Y" | "N">,
              "msgid": <message id: str>,
              "furl": "",
              "fcontype": <"Content" | "File">,
              "ftarget": <"_self" | "_tab">,
              "furgent": <"Y" | "N">,
              "total_record": 42,  # idk
              "fstartdt": <announcement date: str - "DD/MM/YYYY">
            },
            ...
          ],
          "msgdesc": "",
          "total_record": <total announcements: int>
        }
        """
        params = {
            "page": page,
            "limit": limit,
            "msgType": msg_type,
            "act": "list"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXStudentAnnouncement.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_today_taken_attendance(self) -> requests.Response:
        """
        {
          "msg": "success",
          "total": 0,
          "msgdesc": ""
        }
        """
        params = {
            "act": "get-today-total"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXAttendance.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_today_all_attendance(self) -> requests.Response:
        """
        {
          "msg": "",
          "list": [],
          "msgdesc": ""
        }
        """
        params = {
            "act": "get-today-list"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXAttendance.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_course_attendance_history_summary(self) -> requests.Response:
        """
        {
          "msg": "",
          "list": [
            {
              "frate": <attendance rate: float>,
              "fpass": <"Y" | "N">,
              "funits": <course code: str>,
              "fdesc": <course name: str>,
              "fratedis": <rounded attendance rate?: int>
            },
            ...
          ],
          "msgdesc": ""
        }
        """
        params = {
            "act": "get-summary-list"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXAttendance.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_course_attendance_history(self, course_code: str) -> requests.Response:
        """
        {
          "msg": "",
          "clist": [
            {
              "leave": <total number of leave overall: int>,
              "absent": <total number of absence overall: int>,
              "present": <total number of present overall: int>,
              "type": <"P" | "T" | "L">  # Practical, Tutorial, Lecture
            },
            {
              ...
              "type": "T"
            },
            {
              ...
              "type": "L"
            }
          ],
          "list": [
            {
              "date": <date of the class: str - "DD/MM/YYYY">,
              "name": <class teacher name: str>,
              "show": "N",  # idk what is this lmfao
              "time": <time string: str - "mm:ss AM - mm:ss AM">,
              "type": <"P" | "T" | "L">,
              "status": <"P" | "L" | "A">  # Present, Leave, Absent
            },
            ...
          ],
          "msgdesc": ""
        }
        """
        params = {
            "act": "get-details-list",
            "funits": course_code
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXAttendance.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_pending_bill(self) -> requests.Response:
        """
        {
          "msg": "success",
          "total": 0,
          "msgdesc": ""
        }
        """
        params = {
            "act": "get-total-pending"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXStudentBill.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_bill_history(self) -> requests.Response:
        """
        {
          "msg": "",
          "list": [
            {
              "receipts": [
                {
                  "ftype": <month of the receipt initials, capitalized: str>,
                  "frcpno": <payment receipt no>,
                  "frcpdt": <receipt date: str - "DD-MM-YYYY">,
                  "currency": <currency identifier: str - "RM">,
                  "famt": <payment amount: int>
                },
                ...
              ],
              "fstatus": "Paid",  # TODO: go in debt
              "fbilref": <bill reference: str>,
              "billdesc": <bill description: str>,
              "currency": <currency identifier: str - "MYR">,
              "famt": <total payment amount: int>
            },
            ...
          ],
          "msgdesc": ""
        }
        """
        params = {
            "act": "list-history"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXStudentBill.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_profile_photo(self) -> requests.Response:
        """
        {
          "msg": "success",
          "photo": <base64 encoded image: str>,
          "msgdesc": ""
        }
        """
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXGetStudentPhoto.jsp")

    @require_login
    @check_session_valid
    def _update_user_session(self) -> requests.Response:
        # no idea where to use
        payload = {
            "deviceid": "",
            "act": "update"
        }
        return self.session.post("https://app.tarc.edu.my/MobileService/services/AJAXUpdateUserSession.jsp", data=payload)
    
    # def refresh_token(self) -> None:
    #     # no idea where to use
    #     self.session.post("https://app.tarc.edu.my/MobileService/refreshToken")

    @require_login
    @check_session_valid
    def _fetch_class_timetable(self, week: int) -> requests.Response:
        """idk for now
        {
          "duration": "",
          "msg": "",
          "rec": [],
          "weeks": [
            "all"
          ],
          "session": "",
          "direct": [],
          "selected_week": "all",
          "msgdesc": "",
          "holiday": []
        }
        """
        params = {
            "act": "get",
            "week": week
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXStudentTimetable.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_exam_timetable(self) -> requests.Response:
        """idk also
        {
          "msg": "pending",
          "msgdesc": "Closed!"
        }
        """
        params = {
            "act": "list",
            "mversion": 1
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXExamTimetable.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_current_semester_exam_results(self) -> requests.Response:
        """idk
        {
          "msg": "block",
          "msgdesc": ""
        }
        """
        params = {
            "act": "list-current"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXExamResultCurrentList.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_overall_exam_results(self) -> requests.Response:
        """
        {
          "msg": "",
          "rec": {
            "fregkey": <student id: str>,
            "examresult": [
              {
                "ftche": <total credit hours: str - as float>,
                "fengvalue": <english language exit requirements achieved: str>,  # idk
                "examsession": [
                  {
                    "fcgpa": <cgpa: str - as float>,
                    "fsche": <semester credit hours: str - as float>,
                    "ftche": <total credit hours: str - as float>,
                    "courses": [
                      {
                        "fremark": "",
                        "fpapind": "",
                        "fpgrade": "",
                        "fexmtype": "D",
                        "ffailind": "Failed",  # i have no idea what these five fields do
                        "funits": <course code: str>,
                        "fdesc": <course name: str>,
                        "fpaptype": "M",  # idk
                        "fsitting": "1",  # ?
                        "fgrade": <grade: str>
                      },
                      ...
                    ],
                    "fdeanlist": "",
                    "fermstatus": <probably end term?: str - "YYYYMM">,
                    "fexmtype": "D",
                    "display": < : bool>,  # finally a boolean instead of y or n
                    "fsession": <session term: str - "YYYYMM">,
                    "fgpa": <session gpa: str - as float>
                  },
                  ...
                ],
                "fexmtype": "D",
                "fenglabel": "English Language Exit Requirement Achieved",
                "fmuet": ""
              }
            ]
          },
          "msgdesc": ""
        }
        """
        params = {
            "act": "list"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXExamResultCurrentList.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_facilities(self) -> requests.Response:
        """
        {
          "msg": "",
          "eventlist": [
            {
              "fname": "Cyber Centre Discussion Room",
              "id": "F1D823EF-4811-4FEA-8AA2-90E9F666FA06"  # used for bookings
            },
            {
              "fname": "Library Discussion Room / Individual Study Room",
              "id": "78B1476B-6EC0-43FA-8DB7-E2801E4C3A1B"
            },
            {
              "fname": "Sports Facilities",
              "id": "8D7392FB-6BCF-449A-AA79-3F19B607E892"
            }
          ],
          "bookinglist": [],
          "msgdesc": "",
          "msgtype": ""
        }
        """
        params = {
            "act": "get-event-booking-list"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXFacilityBooking.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_facilities_booking_guidelines(self) -> requests.Response:
        """
        {
          "msg": "",
          "list": [
            {
              "fname": "Cyber Centre Discussion Room",
              "id": "B514DE57-873D-4E6D-B589-571CD2E1A6B1",
              "fcontent": "<p><strong>Booking Guidelines:</strong></p>\n<ol>\n<li>Minimum 1 person.&nbsp;<strong>Do not hog</strong> the discussion room if it is not in use.</li>\n<li>Room can be booked 1 day in advance.</li>\n<li>Maximum 2 hours per booking, extension is subject to room availability.</li>\n<li>Room will be assigned based on number of users.</li>\n<li>Cancellation can be done under \"Booking Details Page\".</li>\n<li>A Group Representative is required to make the booking.</li>\n<li>Student <strong>must CHECK-IN / CHECK OUT</strong> at Internet Lab Counter. Students are to <strong>present</strong> their <strong>student ID card</strong> at the lab counter for registration purposes.</li>\n<li>Room booked will be <strong>forfeited after 10 minutes</strong> if no-show. The system will <strong>block</strong> from booking for <strong>all members</strong> for the rest of the day.</li>\n<li>Do not add in / move / remove the furniture inside the discussion room.</li>\n</ol>\n<p>&nbsp;</p>\n<p><strong>NOTE 1 : Discussion rooms are strictly to be used for acadmic purpose only.</strong></p>\n<p><strong>NOTE 2 : Projecting movie from projector is prohibited due to copyright issue.</strong></p>"
            },
            {
              "fname": "Library Discussion Room / Individual Study Room",
              "id": "1B8EA719-3EB1-45F9-9FC7-820A6168235E",
              "fcontent": "<p><strong>Booking Requirements for Discussion Room / Presentation Room:</strong></p>\n<ul>\n<li>A minimum of 2 individuals is required to book the Discussion Room / Presentation Room.</li>\n<li>One member of the group must be designated as the representative responsible for booking the Discussion Room / Presentation Room.</li>\n<li>Room assignment will be automatically determined by the system based on the group's size at the time of booking the Discussion Room / Presentation Room.</li>\n</ul>\n<p>&nbsp;</p>\n<p><strong>General Booking Guidelines:</strong></p>\n<ul>\n<li>Booking can be made 1 day in advance.</li>\n<li>Each booking is restricted to a maximum of 2 hours. An exception is granted for a single extension, subject to room availability on the request time (Refer to the room availability chart prior to requesting an extension from the Circulation staff at the Service Counter).</li>\n<li>Cancellations are possible via the \"Booking Details Page\".</li>\n<li>Reserved rooms will be made available to other eligible users if the booking holder does not appear within 10 minutes. Additionally, the system will prohibit the entire group or individual from making subsequent bookings for the remainder of the day.</li>\n<li>For reservations involving the Discussion Room, Presentation Room, and Individual Study Room, either the Group Representative or the individual who made the booking must complete the Check-in and Check-out process at the Service Counter.</li>\n<li>The Group Representative or the individual who made the booking must present their ID card to the staff in order to receive the room key, which must be returned upon end of booking.</li>\n</ul>"
            },
            {
              "fname": "Sports Facilities",
              "id": "60611E12-3DE6-4C8F-BC13-554B866E1885",
              "fcontent": "<ul>\n<li>Online sports facilities can be booked&nbsp;<strong>two(2)</strong> days in advance.</li>\n<li>All facilities is limited to one booking(min-1 hour/max-2 hours)&nbsp; per court per person per day.</li>\n<li>Check-in/Check-out at the Counter. All users/participants must present their ID cards at the counter upon using sports facilities.</li>\n<li>The booked facilities will be forfeited after 15 minutes if no-show.</li>\n<li>Students who never show up will be blocked for 3 days.</li>\n<li>Whoever breaches the rules will not be allowed to use the facilities in future.</li>\n<li>The authority reserves the right to cancel any booking without prior notice.</li>\n<li>For further information, please call: - TAR UMT Sports Complex <strong>03-41450123</strong> Ext <strong>3570</strong>.</li>\n</ul>"
            }
          ],
          "msgdesc": "",
          "msgtype": ""
        }
        """
        params = {
            "act": "get-guideline-list"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXFacilityBooking.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_facility_venues(self, facility_id: str) -> requests.Response:
        """
        facility_id = "F1D823EF-4811-4FEA-8AA2-90E9F666FA06"
        {
          "msg": "",
          "msgdesc": "",
          "msgtype": "",
          "option": [
            {
              "disabled": false,
              "text": "Discussion Room (1 PC)",
              "value": "4C31BC65-925B-467E-B027-10FF5E57606A"  # used for booking
            },
            {
              "disabled": false,
              "text": "Discussion Room (2 PCs)",
              "value": "508C9BA2-93D5-4B37-A369-E89CC74A6AE8"
            },
            {
              "disabled": false,
              "text": "Discussion Room (2 PCs) : Projector Under Maintenance !",
              "value": "485D2BC5-7156-49C7-8815-130141BCA754"
            },
            {
              "disabled": false,
              "text": "Discussion Room with Projector (2 PCs)",
              "value": "FEF1AD8E-461F-47B8-BB7E-9677CE9FA86E"
            },
            {
              "disabled": false,
              "text": "Discussion Room with Projector (2 PCs) [HDMI]",
              "value": "0C975986-AF70-4336-86A0-5ED424F0B58E"
            }
          ]
        }
        """
        params = {
            "act": "get-venue-type",
            "event_id": facility_id
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXFacilityBooking.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_facility_booking_date_options(self, facility_id: str) -> requests.Response:
        """
        facility_id = "F1D823EF-4811-4FEA-8AA2-90E9F666FA06"
        {
          "msg": "",
          "msgdesc": "",
          "msgtype": "",
          "option": [
            {
              "disabled": false,
              "text": "21/Jan/2024 (Sun)",
              "value": "21/01/2024"
            },
            {
              "disabled": false,
              "text": "22/Jan/2024 (Mon)",
              "value": "22/01/2024"
            }
          ]
        }
        """
        params = {
            "act": "get-booking-date",
            "event_id": facility_id
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXFacilityBooking.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_facility_general_setting(self, facility_id: str) -> requests.Response:
        """no idea what does this do
        facility_id = "F1D823EF-4811-4FEA-8AA2-90E9F666FA06"
        {
          "msg": "",
          "member_required": true,
          "msgdesc": "",
          "msgtype": ""
        }
        """
        params = {
            "act": "get-general-setting",
            "event_id": facility_id
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXFacilityBooking.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_facility_guidelines(self, facility_id: str) -> requests.Response:
        """
        facility_id = "F1D823EF-4811-4FEA-8AA2-90E9F666FA06"
        {
          "msg": "",
          "member_required": true,
          "msgdesc": "",
          "msgtype": "",
          "content": "<p><strong>Terms of Use:</strong></p>\n<ol>\n<li>Read the <strong>Booking Guidelines</strong>.</li>\n<li>Discussion rooms are for&nbsp;<strong>study purposes only</strong>.</li>\n<li><strong>Do not hog</strong> the discussion room if it is not in use.</li>\n<li><strong>Do not lock</strong> the discussion room door</li>\n<li><strong>Foods and beverages are prohibited</strong> in the discussion room.</li>\n<li>Student <strong>must CHECK-IN / CHECK OUT</strong> at Internet Lab Counter.</li>\n<li>Room booked will be <strong>forfeited after 10 minutes</strong> if no-show.</li>\n<li>Students shall discuss softly so as not to disturb other users.</li>\n<li>Remember to take all your belongings with you when you leave the room.</li>\n<li>Always keep the room clean.</li>\n<li>Do not add in / move / remove the furniture inside the discussion room.</li>\n<li>No vandalism is allowed inside the discussion room.</li>\n</ol>\n<p>&nbsp;</p>\n<p><strong>NOTE 1 : Discussion rooms are strictly to be used for acadmic purpose only.</strong></p>\n<p><strong>NOTE 2 : Projecting movie from projector is prohibited due to copyright issue.</strong></p>"
        }
        """
        params = {
            "act": "get-general-setting-form",
            "event_id": facility_id
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXFacilityBooking.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_facility_booking_starting_timeslots(self, facility_id: str) -> requests.Response:
        """
        facility_id = "F1D823EF-4811-4FEA-8AA2-90E9F666FA06"
        {
          "msg": "",
          "msgdesc": "",
          "msgtype": "",
          "option": [
            {
              "disabled": false,
              "text": "08:00 AM",
              "value": "08:00"
            },
            {
              "disabled": false,
              "text": "08:30 AM",
              "value": "08:30"
            },
            ...
            {
              "disabled": false,
              "text": "08:30 PM",
              "value": "20:30"
            }
          ]
        }
        """
        params = {
            "act": "get-booking-time",
            "event_id": facility_id,
            "timetype": "start"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXFacilityBooking.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_facility_booking_ending_timeslots(self, facility_id: str) -> requests.Response:
        """
        facility_id = "F1D823EF-4811-4FEA-8AA2-90E9F666FA06"
        {
          "msg": "",
          "msgdesc": "",
          "msgtype": "",
          "option": [
            {
              "disabled": false,
              "text": "08:30 AM",
              "value": "08:30"
            },
            {
              "disabled": false,
              "text": "09:00 AM",
              "value": "09:00"
            },
            ...
            {
              "disabled": false,
              "text": "09:00 PM",
              "value": "21:00"
            }
          ]
        }
        """
        params = {
            "act": "get-booking-time",
            "event_id": facility_id,
            "timetype": "end"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXFacilityBooking.jsp", params=params)

    @require_login
    @check_session_valid
    def _book_facility(
            self,
            facility_id: str,
            booking_date: str,
            starting_time: str,
            ending_time: str,
            venue_id: str,
            students_id_and_name: Sequence[tuple[str, str]]
    ) -> requests.Response:
        """
        (on failure)
        {
          "msg": "failed",
          "msgdesc": <reason: str>,
          "msgtype": "process"
        }
        """
        payload = {
            "act": "insert",
            "event_id": facility_id,
            "fbkdate": booking_date,  # "DD/MM/YYYY"
            "fstarttime": starting_time,  # "mm:ss" 24-hours format
            "fendtime": ending_time,  # "mm:ss" 24-hours format
            "venuex_type_id": venue_id,
            "fpaxno": len(students_id_and_name) + 1,
            "member_fregkey": [stud[0] for stud in students_id_and_name],
            "member_name": [stud[1] for stud in students_id_and_name]
        }
        return self.session.post("https://app.tarc.edu.my/MobileService/services/AJAXFacilityBooking.jsp", data=payload)

    @require_login
    @check_session_valid
    def _fetch_facility_calendar(self, facility_id: str, date: str, venue_id: str = '', number_of_pax: int = 0) -> requests.Response:
        """
        facility_id = "F1D823EF-4811-4FEA-8AA2-90E9F666FA06"
        date = 21/01/2024
        venue_id = ""
        pax = ""
        {
          "msg": "",
          "note": " <style> .table-note{width:360px;min-height:100px; border-collapse:collapse;border:0;}          .table-note tr {border:0;}         .table-note tr td {border:0;}</style><div style='padding-left:10px;'><table class=\"table-note\">\t<tbody>\t\t<tr>\t\t\t<td>\t\t\t\t<div>\t\t\t\t\t<div style=\"width:16px;height:16px;background-color:#009624\"></div>\t\t\t\t</div>\t\t\t</td>\t\t\t<td  style=\"width:100px\">Available</td>\t\t\t<td>\t\t\t\t<div>\t\t\t\t\t<div style=\"width:16px;height:16px;background-color:#00b0f0;\"></div>\t\t\t\t</div>\t\t\t</td>\t\t\t<td   style=\"width:100px\">Booked</td>\t\t\t<td>\t\t\t\t<div>\t\t\t\t\t<div style=\"width:16px;height:16px;background-color:#d9d9d9;\"></div>\t\t\t\t</div>\t\t\t</td>\t\t\t<td   style=\"width:100px\">Closed</td>\t\t\t</tr>\t</tbody></table></div>",
          "header": "<style>\t.tooptip{position:relative;}   .tooltip span {right:-160px; visibility: hidden;  width: 150px;  background-color: #555;  color: #fff;  text-align: left;  border-radius: 6px;  padding: 5px;  position: absolute;  z-index: 20;   opacity: 0;  transition: opacity 0.3s;} \t.tooltip input {display:none;writing-mode: horizontal-tb !important;}    .tooltip input:checked+span {visibility: visible;opacity: 1;white-space: normal;} \ttable tr td{ font-size:12px;padding:4px;;background-color:#ffffff;color:#000000;}   .table-schedule thead  {position: sticky; top: 0;z-index:10;font-weight:bold;;background-color:#ffffff;color:#000000;}\t.table-schedule thead tr{position: sticky; left: 0;text-align:left;}\t.table-schedule thead [rowspan]{position: sticky; left: 0;text-align:left;z-index:10;;background-color:#ffffff;color:#000000;}\t.table-schedule thead [colspan]{z-index:-1;}   .table-schedule tbody td.side-header {position: sticky; left: 0;text-align:left;;background-color:#ffffff;color:#000000;}\ttr,td{border:1px solid #dddddd;padding:2px;font-size:10px;background-color: white;}   .table-hidden td{padding-top:0 !important;padding-bottom:0 !important;padding-left:8px !important;padding-right:8px !important;border:1px !important;}\t.nowrap{overflow:hidden;white-space: nowrap;text-overflow: ellipsis;max-width:60px}</style><tr><td rowspan=\"2\" >Venue/Time</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">08:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">09:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">10:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">11:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">12:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">01:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">02:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">03:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">04:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">05:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">06:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">07:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">08:00</td></tr><tr style='z-index:-1;'><td colspan=\"2\"  align=\"center\" valign=\"middle\">09:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">10:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">11:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">12:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">01:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">02:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">03:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">04:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">05:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">06:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">07:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">08:00</td><td colspan=\"2\"  align=\"center\" valign=\"middle\">09:00</td></tr><tr class=\"table-hidden\" ><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>",
          "msgdesc": "",
          "content": "<tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC108<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC108 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 1 - 3 <br />Description : 1-3pax room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC109<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC109 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 1 - 3 <br />Description : 1-3pax room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC110<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC110 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 1 - 3 <br />Description : 1-3pax room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC111<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room with Projector (2 PCs) [HDMI] <br />Venue No. : CC111 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 4 - 6 <br />Description : 4-6pax room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC112<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (2 PCs) : Projector Under Maintenance ! <br />Venue No. : CC112 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 4 - 6 <br />Description : 4-6Pax Room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC113<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC113 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 3 - 4 <br />Description : 3-4pax room (2 chairs & 1 sofa)</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC116<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC116 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 1 - 3 <br />Description : 1-3pax room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC117<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room with Projector (2 PCs) [HDMI] <br />Venue No. : CC117 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 4 - 6 <br />Description : 4-6pax room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC118<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room with Projector (2 PCs) <br />Venue No. : CC118 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 4 - 6 <br />Description : 4-6Pax Room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC119<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC119 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 3 - 4 <br />Description : 3-4pax room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC120<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (2 PCs) : Projector Under Maintenance ! <br />Venue No. : CC120 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 4 - 6 <br />Description : 4-6Pax Room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC121<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC121 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 1 - 3 <br />Description : 1-3Pax Room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC122<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (2 PCs) : Projector Under Maintenance ! <br />Venue No. : CC122 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 4 - 7 <br />Description : 4-7Pax Room (6 chairs & 1 sofa)</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC123<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC123 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 1 - 3 <br />Description : 1-3Pax Room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC124<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (2 PCs) <br />Venue No. : CC124 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 4 - 6 <br />Description : 4-6Pax Room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC125<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC125 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 1 - 3 <br />Description : 1-3Pax Room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC128<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (2 PCs) : Projector Under Maintenance ! <br />Venue No. : CC128 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 4 - 7 <br />Description : 4-7Pax Room (6 chairs & 1 sofa)</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC129<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC129 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 1 - 3 <br />Description : 1-3Pax Room</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC130<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (2 PCs) : Projector Under Maintenance ! <br />Venue No. : CC130 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 6 - 8 <br />Description : 6-8Pax Room ( 6chairs & 1 sofa)</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr><tr><td class=\"side-header\"  data-html=\"true\"><label class=\"tooltip\" style=\"position:relative;width:100%;display:block;\">CC131<input type=\"checkbox\"><span class=\"tooltiptext\"> <div>Venue Type : Discussion Room (1 PC) <br />Venue No. : CC131 <br />Location : Cyber Centre,Ground Floor <br />Min/Max Pax : 3 - 5 <br />Description : 3-5Pax Room (3 chairs & 1 sofa)</div></span></label></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td><td  align=\"center\" valign=\"middle\" style=''></td></tr>"
        }
        """
        params = {
            "act": "list",
            "event_id": facility_id,
            "fdate": date,
            "venue_type_id": venue_id,
            "fpaxno": number_of_pax if number_of_pax > 0 else "",
            "mode": "light"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXFacilityCalendar.jsp", params=params)

    @require_login
    @check_session_valid
    def _validate_student(self, student_id: str, student_name: str) -> requests.Response:
        """
        {
          "msg": <"success" | "invalid">,
          "msgdesc": <"" | "Invalid Student ID or Name">,
          "msgtype": ""
        }
        """
        params = {
            "act": "get-booking-time",
            "member_fregkey": student_id,
            "member_name": student_name
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXFacilityBooking.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_vehicle_entry_pass(self) -> requests.Response:
        """me no car ;w;
        {
          "msg": "",
          "list": [],
          "msgdesc": ""
        }
        """
        params = {
            "act": "list"
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXEntryPass.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_emergency_helpline_details(self,campus: CampusID = "KL"):
        """
        {
          "msg": "",
          "campus_desc": "Kuala Lumpur Campus",
          "list": [
            {
              "code": <brief title (not exact title): str>,
              "contact": [
                {
                  "tel_dis": <phone number: str>,
                  "subtitle": <phone number description: str>,
                  "tel": <actual phone number?: str>
                },
                ...
              ],
              "title": <helpline title: str>,
              "icon_link": <image url address: str>
            },
            ...
          ],
          "msgdesc": ""
        }
        """
        params = {
            "act": "list",
            "fcat": "E",
            "fbrncd": campus
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXHelpline.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_general_helpline_details(self, campus: CampusID = "KL"):
        """
        {
          "msg": "",
          "campus_desc": "Kuala Lumpur Campus",
          "list": [
            {
              "code": <brief title (not exact title): str>,
              "contact": [
                {
                  "tel_dis": <phone number: str>,
                  "subtitle": <phone number description: str>,
                  "tel": <actual phone number?: str>
                },
                ...
              ],
              "title": <helpline title: str>,
              "icon_link": <image url address: str>
            },
            ...
          ],
          "msgdesc": ""
        }
        """
        params = {
            "act": "list",
            "fcat": "G",
            "fbrncd": campus
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXHelpline.jsp", params=params)

    @require_login
    @check_session_valid
    def _fetch_campus(self) -> requests.Response:
        """
        {
          "msg": "",
          "campus_list": [
            {
              "display": <campus name: str>,
              "value": <campus identifier: str>
            },
            ...
          ]
          "msgdesc": ""
        }
        """
        params = {
            "act": "campus-list",
        }
        return self.session.get("https://app.tarc.edu.my/MobileService/services/AJAXHelpline.jsp", params=params)

    @require_login
    @check_session_valid
    def _take_attendance(self, attendance_code: str) -> requests.Response:
        """
        {
          "msg": "taruc-ip",
          "msgdesc": "<ip> is an unknown IP address. Please connect to TARUMT's WIFI and submit again."
        }
        """
        payload = {
            "act": "insert",
            "fsigncd": attendance_code,
            "deviceid": "",
            "devicemodel": "",
        }
        return self.session.post("https://app.tarc.edu.my/MobileService/services/AJAXAttendance.jsp", data=payload)
