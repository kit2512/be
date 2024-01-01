from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import Integer, Column, DateTime, Enum, ForeignKey, String, Table, Boolean
from enum import StrEnum
import datetime

from .database import Base

USER_TABLE = "user_table"
EMPLOYEE_TABLE = "employee_table"
ROOM_TABLE = "room_table"
RFID_MACHINE_TABLE = "rfid_machine_table"
CHECKIN_HISTORY_TABLE = "checkin_history_table"
ROOM_EMPLOYEE_TABLE = "room_employee_table"
RFID_CARD_TABLE = "rfid_card_table"


class UserRole(StrEnum):
    manager = "manager"
    employee = "employee"


class User(Base):
    __tablename__ = USER_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now())
    role = Column(Enum(UserRole))
    employee: Mapped["Employee"] = relationship(back_populates="user")
    hashed_password = Column(String(300), nullable=False,)
    first_name = Column(String(30), nullable=False)
    last_name = Column(String(30), nullable=False)
    username = Column(String(100), nullable=False, unique=True)


room_employee_table = Table(
    ROOM_EMPLOYEE_TABLE,
    Base.metadata,
    Column("room_id", Integer, ForeignKey(ROOM_TABLE + ".id"), primary_key=True),
    Column("employee_id", Integer, ForeignKey(EMPLOYEE_TABLE + ".id"), primary_key=True),
    Column("date_created", DateTime, nullable=False, default=datetime.datetime.now()))


class Employee(Base):
    __tablename__ = EMPLOYEE_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    user_id: Mapped[Integer] = mapped_column(ForeignKey(USER_TABLE + ".id"))
    user: Mapped[User] = relationship(back_populates="employee")
    checkin_history: Mapped[List["CheckinHistoryItem"]] = relationship("CheckinHistoryItem", back_populates="employee")
    allowed_rooms: Mapped[List["Room"]] = relationship(secondary=room_employee_table,
                                                       back_populates="allowed_employees")
    card: Mapped["RfidCard"] = relationship(back_populates='employee')


class Room(Base):
    __tablename__ = ROOM_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(200), nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now())
    rfid_machines: Mapped[List["RfidMachine"]] = relationship("RfidMachine", back_populates="room")
    allowed_employees: Mapped[List["Employee"]] = relationship(secondary=room_employee_table,
                                                               back_populates="allowed_rooms")


class RfidMachine(Base):
    __tablename__ = RFID_MACHINE_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(200), nullable=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now())
    room_id: Mapped[Integer] = mapped_column(ForeignKey(ROOM_TABLE + ".id"), nullable=True)
    room: Mapped[Room] = relationship(back_populates="rfid_machines")
    checkin_history: Mapped[List["CheckinHistoryItem"]] = relationship("CheckinHistoryItem", back_populates="rfid_machine")
    allow_checkin = Column(Boolean, nullable=False, default=False)


class RfidCard(Base):
    __tablename__ = RFID_CARD_TABLE

    id = Column(String(100), nullable=False, primary_key=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now())
    employee_id: Mapped[Integer] = mapped_column(ForeignKey(EMPLOYEE_TABLE + '.id'), nullable=True)
    employee: Mapped[Employee] = relationship(back_populates='card')
    checkin_history: Mapped[List['CheckinHistoryItem']] = relationship(back_populates='card')


class CheckinHistoryItem(Base):
    __tablename__ = CHECKIN_HISTORY_TABLE

    id = Column(Integer, nullable=False, primary_key=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now())
    employee_id: Mapped[Integer] = mapped_column(ForeignKey(EMPLOYEE_TABLE + ".id"))
    employee: Mapped[Employee] = relationship(back_populates="checkin_history")
    rfid_machine_id: Mapped[Integer] = mapped_column(ForeignKey(RFID_MACHINE_TABLE + ".id"))
    rfid_machine: Mapped[RfidMachine] = relationship(back_populates="checkin_history")
    allow_checkin = Column(Boolean, nullable=False, default=True)
    card: Mapped[RfidCard] = relationship(back_populates="checkin_history")
    card_id: Mapped[String] = mapped_column(ForeignKey(RFID_CARD_TABLE + '.id'))
