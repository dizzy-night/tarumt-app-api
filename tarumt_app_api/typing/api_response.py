from typing import TypedDict, Literal, NotRequired

type CampusID = Literal["KL", "PP", "PK", "JH", "PH", "SB"]
type YesOrNo = Literal["Y", "N"]
type EmptyStr = str
type ClassType = Literal["P", "T", "L"]  # Practical, Tutorial, Lecture
type AttendanceType = Literal["P", "L", "A"]  # Present, Leave, Absent


class _Class(TypedDict):
    fstaffname: str
    fclasstype: ClassType
    froom: str        # room number
    hour: str         # number of hours, is float
    fstart: str       # starting time, format "hh:mm pp"
    replace: YesOrNo  # is a replacement class?
    fend: str         # ending time, format "hh:mm pp"
    funits: str       # course code
    fdesc: str        # course name
    fweedur: str      # is not empty only when fetching week="all"
                      # the weeks the class runs, exp "1-14"


class _FacilityDetails(TypedDict):
    fname: str  # facility name
    id: str     # facility guid


class _VenueDetails(TypedDict):
    disabled: bool
    text: str   # venue name
    value: str  # venue guid


# class name is usually named like "[func_name][capitalized <msg> message]Response"

class APIResponse(TypedDict):  # all response contain these fields
    msg: Literal["", "success", "failed", "block", "pending"]
    msgdesc: str


class TokenExpired(TypedDict):
    statusCd: Literal["invalid-token"]
    msgdesc: Literal["Token expired. Please login again"]


class LoginSuccessResponse(TypedDict):
    msg: Literal["success"]
    brncd: CampusID
    fullname: str  # student name
    msgdesc: EmptyStr
    userid: str    # student id
    email: str     # student email
    token: str     # session token. need to set to header "X-Auth"


class LoginFailureResponse(TypedDict):
    msg: Literal["failed"]
    msgdesc: str  # reason
    token: EmptyStr


class AppAccessSuccessResponse(TypedDict):
    msg: Literal["success"]
    access: list[str]  # no idea
    msgdesc: EmptyStr


# unsure
class NoticeResponse(TypedDict):
    msg: str
    show: str  # not sure, so far only got literal "N"
    msgdesc: str


class NewAnnouncementCountSuccessResponse(TypedDict):
    msg: Literal["success"]
    total: int
    msgdesc: EmptyStr


class StudentAnnouncementsResponse(TypedDict):
    class Annoucement(TypedDict):
        ftitle: str      # announcement title
        fsender: str     # sender dept
        ftype: Literal["Announcement"]  # so far only seen announcement
        isread: YesOrNo
        msg_id: str
        furl: str  # so far is empty
        fcontype: Literal["Content", "File"]
        ftarget: Literal["_self", "_tab"]
        furgent: YesOrNo
        total_record: int  # same as total_record
        fstartdt: str  # format: DD/MM/YYYY

    msg: str
    list: list[Annoucement]
    msgdesc: EmptyStr
    total_record: int


class TodayAttendanceTakenCountSuccessResponse(TypedDict):
    msg: Literal["success"]
    total: int
    msgdesc: EmptyStr


class TodayAttendanceResponse(TypedDict):
    # TODO: find out
    msg: str
    list: list
    msgdesc: EmptyStr


class CoursesAttendanceHistorySummaryResponse(TypedDict):
    class CourseAttendanceSummary(TypedDict):
        frate: float    # attendance rate
        fpass: YesOrNo  # above 80% rate?
        funits: str     # course code
        fdesc: str      # course name
        fratedis: int   # rounded `frate`

    msg: EmptyStr
    list: list[CourseAttendanceSummary]
    msgdesc: EmptyStr


class CourseAttendanceHistoryResponse(TypedDict):
    class CourseAttendance(TypedDict):
        leave: int    # number of leaves
        absent: int   # number of absences
        present: int  # number of attendances
        type: ClassType

    class CoursePracticalAttendance(CourseAttendance):
        type: Literal["P"]  # noqa

    class CourseTutorialAttendance(CourseAttendance):
        type: Literal["T"]  # noqa

    class CourseLectureAttendance(CourseAttendance):
        type: Literal["L"]  # noqa

    class ClassAttendance(TypedDict):
        date: str                       # format: DD/MM/YYYY
        name: str                       # class tutor name
        show: YesOrNo                   # so far only seen N
        time: str                       # timeslot string, format: hh:mm pp - hh:mm pp
        type: ClassType
        status: AttendanceType

    msg: EmptyStr
    clist: tuple[CoursePracticalAttendance, CourseTutorialAttendance, CourseLectureAttendance]
    list: list[ClassAttendance]
    msgdesc: EmptyStr


class PendingBillCountSuccessResponse(TypedDict):
    msg: Literal["success"]
    total: int
    msgdesc: EmptyStr


class BillHistoryResponse(TypedDict):
    class Bill(TypedDict):
        class Receipt(TypedDict):
            ftype: str     # the initial of the month the receipt is printed, January => J
            frcpno: str    # receipt number
            frcpdt: str    # receipt date, format: DD-MM-YYYY
            currency: str  # currency type
                           # weird inconsistency where RM is used here, but MYR used in a different part
            famt: int      # payment amount

        receipts: list[Receipt]
        fstatus: Literal["Paid"]    # TODO: go in debt
        fbilref: str   # bill reference
        billdesc: str  # bill description
        currency: str  # currency identifier. Note: MYR is used here.
        famt: int      # total payment amount

    msg: EmptyStr
    list: list[Bill]
    msgdesc: EmptyStr


# TODO: not have a profile pic somehow
class ProfilePhotoSuccessResponse(TypedDict):
    msg: Literal["success"]
    photo: str  # base64 encoded image bytes
    msgdesc: EmptyStr


class ClassTimetableResponse(TypedDict):
    class Day(TypedDict(    # noqa
        "Day",
        {"class": list[_Class]}   # very crude way of trying to add key "class" coz python
    ), TypedDict):
        date: NotRequired[str]    # date of the class, format "DD/MM/YYYY"
        dowdesc: str              # the day, example "Monday"
        dates: NotRequired[str]   # just `date` but without YYYY
        dowstdesc: str            # abbreviation of `dowdesc`
        dow: str                  # day of week, as number, 1 as monday 7 as sunday
        holiday: str  # TODO: find out

    duration: str   # total length of the semester, format "DD MMM - DD MMM"
                    # example, "19 Feb - 26 May"
    msg: EmptyStr
    rec: list[Day]
    weeks: list[str]    # the weeks available, ex. ["all", "1", "2", ...]
    session: str        # the session for the timetable, format "YYYYMM"
    direct: list        # TODO: find out
    selected_week: str  # the week used in the params "week", includes the literal 'week' "all"
    msgdesc: EmptyStr
    holiday: list       # TODO: find out


# TODO: wait for exam
class ExamTimetableResponse(TypedDict):
    msg: Literal["pending"]
    msgdesc: Literal["Closed!"]


class CurrentSemesterExamResultResponse(TypedDict):
    class Record(TypedDict):
        class SemesterExamination(TypedDict):
            class CourseResult(TypedDict):
                fpgrade: str
                fexmptype: str
                ffailind: str
                funits: str    # course code
                fdescs: str    # course name
                fpaptype: str
                fsitting: str  # is int
                fgrade: str    # course grade

            fremark: str
            fsche: str        # semester credit hours, is float
            ftche: str        # total accumulated credit hours, is float
            fclass: str
            courses: list[CourseResult]
            ftermstatus: str  # terminating session, format "YYYYMM"
            fexmtype: str
            display: bool
            fremark2: str
            femstatusdesc: str
            femstatus: str
            fcgpa: str        # cgpa, is float
            fsession: str     # current sem session, format "YYYYMM"
            fdaterel: str     # result release date, format "DD <month name all caps> YYYY", ex. "16 FEBRUARY 2024"
            fgpa: str         # sem gpa, is float

        exams: list[SemesterExamination]  # usually 1 per sem

    msg: EmptyStr
    rec: Record
    msgdesc: EmptyStr


class CurrentSemesterExamResultBlockedResponse(TypedDict):
    msg: Literal["block"]
    msgdesc: EmptyStr


# TODO: wait for sem 2 results
class OverallExamResultResponse(TypedDict):
    class Records(TypedDict):
        class SemesterResult(TypedDict):
            class SemesterSummary(TypedDict):
                class CourseResult(TypedDict):
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
                courses: list[CourseResult]
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
        examresult: list[SemesterResult]

    msg: EmptyStr
    rec: Records  # records
    msgdesc: EmptyStr


class FacilitiesListResponse(TypedDict):
    msg: EmptyStr
    eventlist: list[_FacilityDetails]
    bookinglist: list  # idk
    msgdesc: EmptyStr
    msgtype: EmptyStr  # idk


class FacilitiesBookingGuidelinesResponse(TypedDict):
    class Guidelines(_FacilityDetails):
        fcontent: str

    msg: EmptyStr
    list: list[Guidelines]
    msgdesc: EmptyStr
    msgtype: EmptyStr


class FacilityVenuesResponse(TypedDict):
    msg: EmptyStr
    msgdesc: EmptyStr
    msgtype: EmptyStr
    option: list[_VenueDetails]


class FacilityBookingDateOptionsResponse(TypedDict):
    class DateOption(TypedDict):
        disabled: bool
        text: str      # weird date text, format  DD/<month name>/YYYY (<day>)
        value: str     # date, format DD/MM/YYYY

    msg: EmptyStr
    msgdesc: EmptyStr
    msgtype: EmptyStr
    option: list[DateOption]  # can be empty


class FacilityGeneralSettingResponse(TypedDict):
    msg: EmptyStr
    member_required: bool
    msgdesc: EmptyStr
    msgtype: EmptyStr


class FacilityUsageGuidelinesResponse(TypedDict):
    msg: EmptyStr
    member_required: bool
    msgdesc: EmptyStr
    msgtype: EmptyStr
    content: str   # html


class FacilityBookingTimeOptionResponse(TypedDict):
    class TimeOption(TypedDict):
        disabled: bool
        text: str   # time text, format hh:mm pp
        value: str  # time, format HH:mm

    msg: EmptyStr
    msgdesc: EmptyStr
    msgtype: EmptyStr
    option: list[TimeOption]  # can be empty


# TODO: book facilities
class FacilityBookingSuccessResponse(TypedDict):
    ...


class FacilityBookingFailureResponse(TypedDict):
    msg: Literal["Failed"]
    msgdesc: str   # reason
    msgtype: Literal["process"]


class FacilityCalendarResponse(TypedDict):
    msg: EmptyStr
    note: str     # facility calendar legends, html
    header: str   # table css + table header, html + css
    msgdesc: EmptyStr
    content: str  # table body, html


class StudentValidateResponse(TypedDict):
    msg: Literal["success", "invalid"]
    msgdesc: Literal["", "Invalid Student ID or Name"]
    msgtype: str


class EntryPassResponse(TypedDict):
    msg: EmptyStr
    list: list
    msgdesc: EmptyStr


class HelplinesDetailsResponse(TypedDict, total=False):
    class Helpline(TypedDict):
        class ContactDetail(TypedDict):
            tel_dis: str   # phone number
            subtitle: str  # phone number description
            tel: str       # some other number?

        code: str        # brief title, not displayed in app
        contact: list[ContactDetail]
        icon_link: str   # image url address

    msg: EmptyStr
    campus_desc: str  # campus name
    list: list[Helpline]
    msgdesc: EmptyStr


class CampusListsResponse(TypedDict):
    class Campus(TypedDict):
        display: str   # campus name
        value: CampusID

    msg: EmptyStr
    campus_list: list[Campus]
    msgdesc: EmptyStr


class AttendanceTakeInvalidIPResponse(TypedDict):
    msg: Literal["taruc-ip"]
    msgdesc: str   # "<ip> is an unknown IP address. Please connect to TARUMT's WIFI and submit again."


class _ClassAttendance(TypedDict):
    classDetails: str  # "hh:mm pp - hh:mm pp, <venue id>"
    courseDesc: str    # course name
    lectureBy: str     # lecturer name
    courseCode: str    # course code


class AttendanceTakeSuccessResponse(TypedDict(
    "AttendanceTakeSuccessResponse",
    {"class": _ClassAttendance}
)):
    msg: Literal["success"]
    msgdesc: EmptyStr


class AttendanceTakeDuplicatedResponse(TypedDict):
    msg: Literal["duplicated"]
    msgdesc: Literal["The record already exists"]


class AttendanceTakeInvalidCodeResponse(TypedDict):
    msg: Literal["invalid-code"]
    msgddesc: Literal["Invalid code entered or you are not allowed to register this class"]
