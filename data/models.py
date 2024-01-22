from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import Integer, Column, DateTime, Enum, ForeignKey, String, Table, Boolean, Date
import datetime

from .constants import *
from .database import Base
from .schemas import DayOffGet


class User(Base):
    __tablename__ = USER_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now(tz=datetime.timezone(
        datetime.timedelta(hours=7))))
    role = Column(Enum(UserRole))
    employee: Mapped["Employee"] = relationship(back_populates="user")
    hashed_password = Column(String(300), nullable=False, )
    first_name = Column(String(30), nullable=False)
    last_name = Column(String(30), nullable=False)
    username = Column(String(100), nullable=False, unique=True)


room_employee_table = Table(
    ROOM_EMPLOYEE_TABLE,
    Base.metadata,
    Column("room_id", Integer, ForeignKey(ROOM_TABLE + ".id"), primary_key=True),
    Column("employee_id", Integer, ForeignKey(EMPLOYEE_TABLE + ".id"), primary_key=True),
    Column("date_created", DateTime, nullable=False, default=datetime.datetime.now(tz=datetime.timezone(
        datetime.timedelta(hours=7)))))


class Employee(Base):
    __tablename__ = EMPLOYEE_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    user_id: Mapped[Integer] = mapped_column(ForeignKey(USER_TABLE + ".id"))
    user: Mapped[User] = relationship(back_populates="employee")
    checkin_history: Mapped[List["CheckinHistoryItem"]] = relationship("CheckinHistoryItem", back_populates="employee")
    allowed_rooms: Mapped[List["Room"]] = relationship(secondary=room_employee_table,
                                                       back_populates="allowed_employees")
    card: Mapped["RfidCard"] = relationship(back_populates='employee')
    salary = Column(Integer, nullable=False, default=0)
    days_off: Mapped[List['DayOff']] = relationship("DayOff", back_populates="approved_by",
                                                    primaryjoin='Employee.id == DayOff.approved_by_id')


class Room(Base):
    __tablename__ = ROOM_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(200), nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now(tz=datetime.timezone(
        datetime.timedelta(hours=7))))
    rfid_machines: Mapped[List["RfidMachine"]] = relationship("RfidMachine", back_populates="room")
    allowed_employees: Mapped[List["Employee"]] = relationship(secondary=room_employee_table,
                                                               back_populates="allowed_rooms")


class RfidMachine(Base):
    __tablename__ = RFID_MACHINE_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(200), nullable=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now(tz=datetime.timezone(
        datetime.timedelta(hours=7))))
    room_id: Mapped[Integer] = mapped_column(ForeignKey(ROOM_TABLE + ".id"), nullable=True)
    room: Mapped[Room] = relationship(back_populates="rfid_machines")
    checkin_history: Mapped[List["CheckinHistoryItem"]] = relationship("CheckinHistoryItem",
                                                                       back_populates="rfid_machine")
    allow_checkin = Column(Boolean, nullable=False, default=False)


class RfidCard(Base):
    __tablename__ = RFID_CARD_TABLE

    id = Column(String(100), nullable=False, primary_key=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now(tz=datetime.timezone(
        datetime.timedelta(hours=7))))
    employee_id: Mapped[Integer] = mapped_column(ForeignKey(EMPLOYEE_TABLE + '.id'), nullable=True)
    employee: Mapped[Employee] = relationship(back_populates='card')
    checkin_history: Mapped[List['CheckinHistoryItem']] = relationship(back_populates='card')


class CheckinHistoryItem(Base):
    __tablename__ = CHECKIN_HISTORY_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now(tz=datetime.timezone(
        datetime.timedelta(hours=7))))
    employee_id: Mapped[Integer] = mapped_column(ForeignKey(EMPLOYEE_TABLE + ".id"))
    employee: Mapped[Employee] = relationship(back_populates="checkin_history")
    rfid_machine_id: Mapped[Integer] = mapped_column(ForeignKey(RFID_MACHINE_TABLE + ".id"))
    rfid_machine: Mapped[RfidMachine] = relationship(back_populates="checkin_history")
    allow_checkin = Column(Boolean, nullable=False, default=True)
    card: Mapped[RfidCard] = relationship(back_populates="checkin_history")
    card_id: Mapped[String] = mapped_column(ForeignKey(RFID_CARD_TABLE + '.id'))


class DayOff(Base):
    __tablename__ = DAYS_OFF_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    employee_id: Mapped[Integer] = mapped_column(ForeignKey(EMPLOYEE_TABLE + ".id"))
    employee: Mapped[Employee] = relationship(back_populates="days_off", foreign_keys='DayOff.employee_id')
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now(tz=datetime.timezone(
        datetime.timedelta(hours=7))))
    reason = Column(String(200), nullable=False)
    approved_by_id: Mapped[Integer] = mapped_column(ForeignKey(EMPLOYEE_TABLE + ".id"), nullable=True)
    approved_by: Mapped[Employee] = relationship("Employee", back_populates='days_off',
                                                 foreign_keys='DayOff.approved_by_id')
    type: Mapped[DayOffType] = Column(Enum(DayOffType), nullable=False)

    @property
    def is_approved(self):
        return self.approved_by_id is not None

    @property
    def total_hours(self):
        return (self.end_date.total_seconds() - self.start_date.total_seconds())() / 3600

    @property
    def day_off_get(self):

        return DayOffGet(
            id=self.id,
            employee_id=self.employee_id,
            start_date=self.start_date,
            end_date=self.end_date,
            date_created=self.date_created,
            reason=self.reason,
            approved_by_id=self.approved_by_id,
            type=self.type,
        )

