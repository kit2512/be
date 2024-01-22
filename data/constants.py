from enum import StrEnum

WORKDAY_START_TIME = 9
WORKDAY_END_TIME = 17


USER_TABLE = "user_table"
EMPLOYEE_TABLE = "employee_table"
ROOM_TABLE = "room_table"
RFID_MACHINE_TABLE = "rfid_machine_table"
CHECKIN_HISTORY_TABLE = "checkin_history_table"
ROOM_EMPLOYEE_TABLE = "room_employee_table"
RFID_CARD_TABLE = "rfid_card_table"
DAYS_OFF_TABLE = "days_off_table"


class UserRole(StrEnum):
    manager = "manager"
    employee = "employee"


class DayOffType(StrEnum):
    paid = "paid"
    unpaid = "unpaid"
