from datetime import datetime, date, timezone, timedelta
from typing import Optional, List

from pydantic import BaseModel

from data.models import UserRole


class UserBase(BaseModel):
    username: str
    date_created: Optional[datetime] = datetime.now(tz=timezone(timedelta(hours=7)))
    role: UserRole
    first_name: str
    last_name: str


class User(UserBase):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True


class UserGet(UserBase):
    id: int


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: str


class EmployeeBase(BaseModel):
    pass


class Employee(BaseModel):
    id: int
    user_id: int
    user: UserGet
    checkin_history: List["CheckinHistoryItem"] = []
    allowed_rooms: List["Room"] = []
    card: Optional['RfidCard'] = None

    class Config:
        from_attributes = True


class EmployeeCreate(EmployeeBase):
    first_name: str
    last_name: str
    username: str
    password: str
    role: UserRole = UserRole.employee
    allowed_rooms: List[int] = []


class CheckinHistoryItemCreate(BaseModel):
    rfid_machine_id: int
    card_id: str | None


class RoomBase(BaseModel):
    name: str
    date_created: Optional[datetime] = datetime.now(tz=timezone(timedelta(hours=7)))


class Room(RoomBase):
    id: int
    allowed_employees: List[Employee] = []
    rfid_machines: List["RfidMachine"] = []

    class Config:
        from_attributes = True


class RoomCreate(RoomBase):
    allowed_employees: Optional[List[int]] = []
    rfid_machines: Optional[List[int]] = []


class RfidMachineBase(BaseModel):
    name: str | None = None
    allow_checkin: Optional[bool] = False


class RfidMachine(RfidMachineBase):
    id: int
    room_id: Optional[int] = None
    room: Optional[Room] = None
    checkin_history: Optional[List["CheckinHistoryItemGet"]] = None
    date_created: Optional[datetime] = datetime.now(tz=timezone(timedelta(hours=7)))

    class Config:
        from_attributes = True


class RfidMachineCreate(RfidMachineBase):
    room_id: int


class CheckinHistoryItemGet(CheckinHistoryItemCreate):
    id: int
    allow_checkin: bool
    date_created: datetime
    room_id: int
    employee_id: int


class CheckinHistoryItemBase(BaseModel):
    allow_checkin: bool


class CheckinHistoryItem(CheckinHistoryItemBase):
    id: int
    employee_id: int
    employee: Employee
    rfid_machine_id: int
    rfid_machine: RfidMachine
    date_created: Optional[datetime] = datetime.now(tz=timezone(timedelta(hours=7)))

    class Config:
        from_attributes = True


class RfidCardBase(BaseModel):
    id: str
    date_created: datetime = datetime.now(tz=timezone(timedelta(hours=7)))


class RfidCardCreate(RfidCardBase):
    employee_id: int | None = None


class RfidCardGet(RfidCardCreate):
    pass


class RfidCard(RfidCardBase):
    employee: Employee | None = None
    employee_id: int | None = None

    class Config:
        from_attributes = True


class EmployeeGet(BaseModel):
    id: int
    user_id: int
    user: UserGet
    checkin_history: List["CheckinHistoryItemGet"] = []
    allowed_rooms: List["Room"] = []
    card: RfidCardGet | None = None


class EmployeeUpdateRequest(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    username: Optional[str]
    password: Optional[str]
    role: Optional[UserRole]
    allowed_rooms: Optional[List[int]] = []


class EmployeeAssignRooms(BaseModel):
    employee_id: int
    room_ids: List[int]


class RoomAssignEmployees(BaseModel):
    room_id: int
    employee_ids: List[int]


class WorkDay(BaseModel):
    date: date
    start_time: datetime
    end_time: datetime
    total_hours: float


class WorkDaysResponse(BaseModel):
    work_days: List[WorkDay]
    total_hours: float
    punishment_hours: float
    employee_id: int
    start_date: Optional[date]
    end_date: Optional[date]


class WorkdayRequest(BaseModel):
    employee_id: int
    start_date: Optional[date]
    end_date: Optional[date]


class DayOffBase(BaseModel):
    start_date: date
    end_date: date
    reason: str


class DayOff(DayOffBase):
    id: int
    employee_id: int
    employee: Employee
    date_created: datetime = datetime.now(tz=timezone(timedelta(hours=7)))
    approved_by_id: int | None = None
    approved_by: Employee | None = None


class DayOffCreate(DayOffBase):
    employee_id: int


class DayOffGet(DayOff):
    pass
