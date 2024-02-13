from typing import TypedDict, Literal, Sequence

type CampusID = Literal["KL", "PP", "PK", "JH", "PH", "SB"]
type YesOrNo = Literal["Y", "N"]


class APIResponse(TypedDict):
    msg: str
    msgdesc: str


class SuccessfulAPIResponse(APIResponse):
    msg: Literal["success"]


class FailedAPIResponse(APIResponse):
    msg: Literal["failed"]


class BlockedAPIResponse(APIResponse):
    msg: Literal["block"]


class PendingAPIResponse(APIResponse):
    msg: Literal["pending"]


class TokenExpired(FailedAPIResponse):
    statusCd: Literal["invalid-token"]
    msgdesc: Literal["Token expired. Please login again"]


class LoginSuccess(SuccessfulAPIResponse):
    brncd: CampusID
    fullname: str  # student name


class LoginFailure(FailedAPIResponse):
    token: str    # is empty


type LoginResponse = LoginSuccess | LoginFailure


class AppAccess(SuccessfulAPIResponse):
    access: list[str]  # list of app accesses


# unsure
class StudentNotice(APIResponse):
    show: str  # not sure, so far only got literal "N"


class StudentAnnouncementCount(SuccessfulAPIResponse):
    total: int


class StudentAnnouncements(APIResponse):
    class AnnoucementData(TypedDict):
        ftitle: str
        fsender: str
        ftype: Literal["Announcement"]  # so far only seen announcement
        isread: YesOrNo
        msg_id: str
        furl: str   # so far is empty
        fcontype: Literal["Content", "File"]
        ftarget: Literal["_self", "_tab"]
        furgent: YesOrNo
        total_record: int  # idk
        fstartdt: str  # format: DD/MM/YYYY

    list: Sequence[AnnoucementData]
    total_record: int


class TodayAttendanceTakenCount(SuccessfulAPIResponse):
    total: int


class TodayAttendance(APIResponse):
    # TODO: find out
    list: Sequence


class CoursesAttendanceHistorySummary(APIResponse):
    class CourseAttendanceSummary(TypedDict):
        frate: float    # attendance rate
        fpass: YesOrNo  # above 80% rate?
        funits: str     # course code
        fdesc: str      # course name
        fratedis: int   # rounded `frate`

    list: Sequence[CourseAttendanceSummary]


class CourseAttendanceHistory(APIResponse):
    class CourseAttendance(TypedDict):
        leave: int    # number of leaves
        absent: int   # number of absences
        present: int  # number of attendances
        type: str

    class CoursePracticalAttendance(CourseAttendance):
        type: Literal["P"]

    class CourseTutorialAttendance(CourseAttendance):
        type: Literal["T"]

    class CourseLectureAttendance(CourseAttendance):
        type: Literal["L"]

    class ClassAttendance(TypedDict):
        date: str                       # format: DD/MM/YYYY
        name: str                       # class tutor name
        show: YesOrNo                   # so far only seen N
        time: str                       # timeslot string, format: hh:mm pp - hh:mm pp
        type: Literal["P", "T", "L"]    # Practical, Tutorial, Lecture
        status: Literal["P", "L", "A"]  # Present, Leave, Absent

    clist: tuple[CoursePracticalAttendance, CourseTutorialAttendance, CourseLectureAttendance]
    list: Sequence[ClassAttendance]


class PendingBillCount(SuccessfulAPIResponse):
    total: int


class BillHistory(APIResponse):
    class Bill(TypedDict):
        class Receipt(TypedDict):
            ftype: str     # the initial of the month the receipt is printed, January => J
            frcpno: str    # receipt number
            frcpdt: str    # receipt date, format: DD-MM-YYYY
            currency: str  # currency type
                           # weird inconsistency where RM is used here, but MYR used in a different part
            famt: int      # payment amount

        receipts: Sequence[Receipt]
        fstatus: Literal["Paid"]    # TODO: go in debt
        fbilref: str   # bill reference
        billdesc: str  # bill description
        currency: str  # currency identifier. Note: MYR is used here.
        famt: int      # total payment amount

    list: Sequence[Bill]


# TODO: not have a profile pic somehow
class ProfilePhoto(SuccessfulAPIResponse):
    photo: str  # base64 encoded image bytes


# TODO: unfinished, have classes
class ClassTimetable(APIResponse):
    duration: str
    rec: Sequence
    weeks: Sequence
    session: str
    direct: Sequence
    selected_week: str
    holiday: Sequence


# TODO: wait for exam
class ExamTimetable(TypedDict):
    msg: Literal["pending"]
    msgdesc: Literal["Closed!"]


# TODO: wait for exam results
class CurrentSemesterExamResults(APIResponse):
    ...


# TODO: wait for sem 2 results
class OverallExamResults(APIResponse):
    class Records(TypedDict):
        class SemesterResults(TypedDict):
            class SemesterSummary(TypedDict):
                class CourseResults(TypedDict):
                    fremark: str   # remark, idk
                    fpapind: str   # idk
                    fpgrade: str   # idk
                    fexmtype: str  # idk
                    ffailind: str  # idk
                    funits: str    # course code
                    fdesc: str     # course name
                    fpaptype: str  # idk
                    fsitting: str  # idk, int
                    fgrade: str    # grade, A+, A, B+, ...

                fcgpa: str      # cgpa, float
                fsche: str      # semester credit hours, float
                ftche: str      # total credit hours, float
                courses: Sequence[CourseResults]
                fdeanlist: str   # idk
                fermstatus: str  # final sem term?, format YYYYMM
                fexmtype: str    # idk
                display: bool    # idk
                fsession: str    # current sem term, format YYYYMM
                fgpa: str        # session gpa, float

            ftche: str       # total credit hour, float
            fengvalue: str   # english language exit requirements achieved. TODO: idk
            examsession: tuple[SemesterSummary]  # its literally an one element tuple wtf
            fexmtype: str    # idk
            fenglabel: Literal["English Language Exit Requirement Achieved"]
            fmuet: str       # idk

        fregkey: str  # student id
        examresult: Sequence[SemesterResults]

    rec: Records  # records


class _Facility(TypedDict):
    fname: str  # facility name
    id: str     # facility guid


class FacilitiesList(APIResponse):
    eventlist: Sequence[_Facility]
    msgtype: str  # idk


class FacilitiesBookingGuidelines(APIResponse):
    class Guidelines(_Facility):
        fcontent: str

    list: Sequence[Guidelines]
    msgtype: str


class FacilityVenueTypes(APIResponse):
    class VenueType(TypedDict):
        disabled: bool
        text: str   # venue name
        value: str  # venue guid

    msgtype: str
    option: Sequence[VenueType]


class FacilityBookingDates(APIResponse):
    class BookingDate(TypedDict):
        disabled: bool
        text: str      # weird date text, format  DD/<month name>/YYYY (<day>)
        value: str     # date, format DD/MM/YYYY

    msgtype: str
    option: Sequence[BookingDate]


# TODO: find out
class FacilityGeneralSetting(APIResponse):
    member_required: bool
    msgtype: str


class FacilityUsageGuidelines(APIResponse):
    member_required: bool
    msgtype: str
    content: str   # html


class FacilityBookingTimeslots(APIResponse):
    class Timeslot(TypedDict):
        disabled: bool
        text: str   # time text, format hh:mm pp
        value: str  # time, format HH:mm

    msgtype: str
    option: Sequence[Timeslot]


# TODO: book facilities
class FacilityBookingSuccess(SuccessfulAPIResponse):
    ...


class FacilityBookingFailure(FailedAPIResponse):
    msgtype: Literal["process"]


class FacilityCalendar(APIResponse):
    note: str     # facility calendar legends, html
    header: str   # css
    content: str  # calendar, html


class StudentValidate(TypedDict):
    msg: Literal["success", "invalid"]
    msgdesc: Literal["", "Invalid Student ID or Name"]
    msgtype: str


# TODO: have vehicle pass
class VehicleEntryPass(APIResponse):
    list: Sequence


class HelplinesDetails(APIResponse):
    class Helpline(TypedDict):
        class ContactDetails(TypedDict):
            tel_dis: str   # phone number
            subtitle: str  # phone number description
            tel: str       # some other number?

        code: str        # brief title, not displayed in app
        contact: Sequence[ContactDetails]
        icon_link: str   # image url address

    campus_desc: str  # campus name
    list: Sequence[Helpline]


class CampusLists(APIResponse):
    class Campus(TypedDict):
        display: str   # campus name
        value: CampusID

    campus_list: Sequence[Campus]


# TODO: take an attendance
class AttendanceTakeFailure(FailedAPIResponse):
    msg: Literal["taruc-ip"]
    msgdesc: str   # "<ip> is an unknown IP address. Please connect to TARUMT's WIFI and submit again."


type AttendanceTakeResponse = AttendanceTakeFailure
