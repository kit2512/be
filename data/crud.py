from datetime import timezone, timedelta

import sqlalchemy.exc
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth.utils import get_password_hash
from data import models
from data.schemas import *


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_employee(db: Session, employee_id: int):
    db_employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if db_employee:
        return db_employee
    return False


def get_employee_by_user_id(db: Session, user_id: int):
    return db.query(models.Employee).filter(models.Employee.user_id == user_id).first()


def create_user(db: Session, user: UserCreate):
    db_user = models.User(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        date_created=user.date_created,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_rooms_by_ids(db: Session, room_ids: List[int]):
    db_rooms = []
    for room_id in room_ids:
        db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
        if not db_room:
            raise HTTPException(400, detail="No room with id {} found".format(room_id))
        db_rooms.append(db_room)
    return db_rooms


def create_employee(db: Session, employee: EmployeeCreate):
    try:
        db_employee = models.Employee()
        user_info = UserCreate(
            username=employee.username,
            first_name=employee.first_name,
            last_name=employee.last_name,
            password=employee.password,
            role=employee.role,
        )
        db_user = create_user(db, user_info)
        db_employee.user = db_user
        db_employee.user_id = db_user.id
        db_employee.allowed_rooms = get_rooms_by_ids(db, room_ids=employee.allowed_rooms)
        db_employee.salary = employee.salary
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee
    except sqlalchemy.exc.IntegrityError:
        raise HTTPException(400, detail="username already taken")


def delete_employee(db: Session, employee_id: int):
    db_employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if db_employee:
        db.delete(db_employee)
        db.delete(db_employee.user)
        db.commit()
        return db_employee
    raise HTTPException(404, detail="No user found with id {}".format(employee_id))


def create_room(db: Session, new_room: RoomCreate):
    db_room = models.Room(**new_room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


def get_room(db: Session, room_id: int):
    return db.query(models.Employee).filter(models.Room.id == room_id).first()


def delete_room(db: Session, room_id: int):
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if db_room:
        db_room.allowed_employees[:] = []
        db_room.rfid_machines[:] = []
        db.commit()
        db.delete(db_room)
        db.commit()
        return db_room
    return False


def create_rfid_machine(db: Session, new_rfid: RfidMachineCreate):
    db_rfid = models.RfidMachine(**new_rfid.model_dump())
    db.add(db_rfid)
    db.commit()
    db.refresh(db_rfid)
    return db_rfid


def get_rfid_machine(db: Session, rfid_id: int):
    db_rfid = db.query(models.RfidMachine).filter(models.RfidMachine.id == rfid_id).first()
    if not db_rfid:
        return False
    return db_rfid


def delete_rfid_machine(db: Session, rfid_id: int):
    db_rfid = db.query(models.RfidMachine).filter(models.RfidMachine.id == rfid_id).first()
    if db_rfid:
        db.delete(db_rfid)
        db.commit()
        return db_rfid
    return False


def create_checkin_history_item(db: Session, new_checkin_item: CheckinHistoryItemCreate):
    db_employee = db.query(models.Employee).join(models.RfidCard,
                                                 models.RfidCard.employee_id == models.Employee.id).filter(
        models.RfidCard.id == new_checkin_item.card_id).first()
    if not db_employee:
        raise HTTPException(400, detail="No employee with card id {}".format(new_checkin_item.card_id))
    db_rfid = get_rfid_machine(db, rfid_id=new_checkin_item.rfid_machine_id)
    if not db_rfid:
        raise HTTPException(400, detail="No RFID machine with id {}".format(new_checkin_item.rfid_machine_id))
    if db_rfid.room not in db_employee.allowed_rooms:
        raise HTTPException(403, "Emploee not allowed to enter room!")
    db_checkin = models.CheckinHistoryItem(
        employee_id=db_employee.id,
        rfid_machine_id=new_checkin_item.rfid_machine_id,
        allow_checkin=db_rfid.allow_checkin,
        rfid_machine=db_rfid,
        employee=db_employee,
        card_id=new_checkin_item.card_id,
        date_created=datetime.now(tz=timezone(timedelta(hours=7))),
    )
    try:
        db.add(db_checkin)
        db.commit()
        db.refresh(db_checkin)
        return db_checkin
    except Exception:
        raise HTTPException(500, detail="Internal server error")


def assign_room_emp(db: Session, employee_id: int, room_ids: List[int]):
    db_employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(404, detail="Unable to find employee with id {}".format(employee_id))
    db_rooms: List[models.Room] = []
    for room_id in room_ids:
        db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
        if not db_room:
            raise HTTPException(status_code=404, detail="Unable to find room with id {}".format(room_id))
        db_rooms.append(db_room)
    db_employee.allowed_rooms[:] = []
    for room in db_rooms:
        db_employee.allowed_rooms.append(room)
    db.commit()


def assign_emp_room(db: Session, room_id: int, employee_ids: List[int]):
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        raise HTTPException(404, detail="Unable to find room with id {}".format(room_id))
    db_employees: List[models.Employee] = []
    for employee_id in employee_ids:
        db_employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
        if not db_employee:
            raise HTTPException(status_code=404, detail="Unable to find employee with id {}".format(employee_id))
        db_employees.append(db_employee)
    db_room.allowed_employees[:] = []
    for employee in db_employees:
        db_room.allowed_employees.append(employee)
    db.commit()


def assign_rfid_room(db: Session, room_id: int, rfid_ids: List[int]):
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        raise HTTPException(404, detail="Unable to find room with id {}".format(id))
    db_rfids: List[models.RfidMachine] = []
    for rfid_id in rfid_ids:
        db_rfid = db.query(models.RfidMachine).filter(models.RfidMachine.id == rfid_id).first()
        if not db_rfid:
            raise HTTPException(404, detail="Unable to find rfid with id {}".format(rfid_id))
        db_rfids.append(db_rfid)
    db_room.rfid_machines[:] = []

    for db_rfid in db_rfids:
        db_room.rfid_machines.append(db_rfid)
    db.commit()


def get_employees(db: Session, room_id: int | None = None):
    if room_id:
        return db.query(models.Employee).select_from(models.Room).join(models.Room.allowed_employees).filter(
            models.Room.id == room_id if room_id else True).all()
    return db.query(models.Employee).all()


def get_rooms(db: Session, employee_id: int | None = None):
    if employee_id:
        return db.query(models.Room).select_from(models.Employee).join(models.Employee.allowed_rooms).filter(
            models.Employee.id == employee_id if employee_id else True).all()
    return db.query(models.Room).all()


def get_rfids(db: Session, room_id: int | None = None):
    query = db.query(models.RfidMachine)
    if room_id:
        query = query.filter(models.RfidMachine.room_id == room_id)
    return query.all()


def get_checkin_history_by_employee(db: Session, emp_id: int):
    db_checkin_history = db.query(models.CheckinHistoryItem).filter(
        models.CheckinHistoryItem.employee_id == emp_id).all()
    return db_checkin_history


def get_checkin_history(db: Session, room_id: int | None = None, rfid_id: int | None = None,
                        employee_id: int | None = None, card_id: str | None = None):
    query = db.query(models.CheckinHistoryItem)
    if room_id:
        query = query.join(models.RfidMachine, models.RfidMachine.room_id == room_id)
    if employee_id:
        query = query.filter(models.CheckinHistoryItem.employee_id == employee_id)
    if rfid_id:
        query = query.filter(models.CheckinHistoryItem.rfid_machine_id == rfid_id)
    if card_id:
        query = query.filter(models.CheckinHistoryItem.card_id == card_id)
    return query.all()


def create_card(db: Session, new_card: RfidCardCreate):
    db_card = db.query(models.RfidCard).filter(models.RfidCard.id == new_card.id).first()
    if db_card:
        raise HTTPException(400, "Card already exists")
    db_card = models.RfidCard(
        **new_card.model_dump()
    )
    db.add(db_card)
    if new_card.employee_id:
        db_employee = db.query(models.Employee).filter(models.Employee.id == new_card.employee_id).first()
        if db_employee:
            if db_employee.card:
                raise HTTPException(400, detail="Employee already has a card")
            else:
                db_employee.card = db_card
        else:
            raise HTTPException(400, detail="Unable to find employee with id {}".format(new_card.employee_id))
    db.commit()
    db.refresh(db_card)
    return db_card


def get_cards(is_available: bool, db: Session):
    query = db.query(models.RfidCard)
    if is_available:
        query = query.filter(models.RfidCard.employee_id == None)
    db_cards = query.all()
    return db_cards


def assign_card(db: Session, card_id: str, employee_id: int):
    db_card = db.query(models.RfidCard).filter(models.RfidCard.id == card_id).first()
    db_employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not db_card or not db_employee:
        raise HTTPException(400, detail="Invalid employee id or card id")
    db_card.employee = db_employee
    db_card.employee_id = db_employee.id
    db.commit()
    db.refresh(db_card)
    return db_card


def delete_card(db: Session, id: str):
    db_card = db.query(models.RfidCard).filter(models.RfidCard.id == id).first()
    if db_card:
        db_card.employee = None
        db_card.employee_id = None
        db.delete(db_card)
        db.commit()
        return db_card


def get_day_hours(start_time: datetime, end_time: datetime) -> float:
    if start_time.date() != end_time.date():
        raise HTTPException(400, "Start time and end time must be in the same day")
    if (end_time - start_time).total_seconds() <= 0:
        return 0
    work_start_time = start_time.replace(hour=8, minute=0, second=0) if start_time.hour < 8 else start_time
    work_end_time = end_time.replace(hour=17, minute=0, second=0) if end_time.hour > 17 else end_time
    lunch_start_time = start_time.replace(hour=12, minute=0, second=0) if start_time.hour < 12 else start_time
    lunch_end_time = end_time.replace(hour=13, minute=0, second=0) if end_time.hour > 13 else end_time
    morning_hours = lunch_start_time - work_start_time
    afternoon_hours = work_end_time - lunch_end_time
    return round((morning_hours.total_seconds() + afternoon_hours.total_seconds()) / 3600, 2)


def daterange(start_date, end_date) -> List[date]:
    dates = []
    for n in range(int((end_date - start_date).days + 1)):
        dates.append(start_date + timedelta(n))
    return dates


def weekday_hours_between_dates(date1: date, date2: date) -> float:
    # Initialize a counter for weekdays
    weekdays = 0
    # Loop from date1 to date2
    for date_item in daterange(date1, date2):
        if date_item.weekday() < 5:
            weekdays += 1
    # Return the number of weekdays
    return weekdays * 8


def get_emp_work_hour(db: Session, emp_id: int, start_date: int | None, end_date: int | None) -> WorkDaysResponse:
    db_employee = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not db_employee:
        raise HTTPException(404, detail="No employee with id {}".format(emp_id))
    results = db.execute(
        text(
            'select date(date_created) as date, min(date_created) as start_time, max(date_created) as end_time from checkin_history_table where employee_id = ' + str(
                emp_id) + ' group by date(date_created) order by date(date_created) asc')
    ).all()
    data = []
    for result in results:
        if (start_date and result[0] < start_date) or (end_date and result[0] > end_date) or (
                result[0] > datetime.now().date()) or (result[1] is None or result[2] is None) or (
                result[0].weekday() > 4):
            continue
        checkin_date = result[0]
        db_day_off = db.query(models.DayOff).filter(models.DayOff.employee_id == emp_id).filter(
            models.DayOff.start_date <= checkin_date).filter(models.DayOff.end_date >= checkin_date).first()
        data.append(WorkDay(date=result[0], start_time=result[1], end_time=result[2],
                            total_hours=get_day_hours(result[1], result[2], ),
                            day_off=db_day_off.day_off_get if db_day_off else None))
    total_hours = sum([x.total_hours if (x.day_off is None) else 0 for x in data])
    weekday_hours = 0 if not data else weekday_hours_between_dates(data[0].date, data[-1].date)
    return WorkDaysResponse(
        work_days=data,
        total_hours=total_hours,
        punishment_hours=round(weekday_hours - total_hours, 2),
        employee_id=emp_id,
        start_date=start_date,
        end_date=end_date,
        paid_amount=db_employee.salary * total_hours,
    )


def create_days_off(db: Session, days_off: DayOffCreate):
    db_employee = get_employee(db, days_off.employee_id)
    if not db_employee:
        raise HTTPException(404, detail="No employee with id {}".format(days_off.employee_id))
    db_day_off = models.DayOff(
        start_date=days_off.start_date,
        end_date=days_off.end_date,
        reason=days_off.reason,
        employee_id=days_off.employee_id,
        type=days_off.type,
    )

    date_range = daterange(days_off.start_date, days_off.end_date)
    print(date_range)
    db_days_off = db.query(models.DayOff).filter(models.DayOff.employee_id == days_off.employee_id).all()
    for db_day_off_item in db_days_off:
        print(db_day_off_item.start_date, db_day_off_item.end_date)
        is_start_valid = db_day_off_item.start_date not in date_range
        is_end_valid = db_day_off_item.end_date not in date_range
        print(is_start_valid, is_end_valid)
        if not is_start_valid or not is_end_valid:
            raise HTTPException(400, detail="Employee already has a day off on {}".format(db_day_off_item.start_date))
    db.add(db_day_off)
    db.commit()
    db.refresh(db_day_off)
    return db_day_off


def get_days_off(db: Session, employee_id: int | None = None, approved: bool | None = None, ):
    query = db.query(models.DayOff)
    if employee_id:
        query = query.filter(models.DayOff.employee_id == employee_id)
    if approved is not None:
        query = query.filter(
            models.DayOff.approved_by_id is not None if approved else models.DayOff.approved_by_id is None)
    return query.all()


def update_days_off(db: Session, days_off: DayOffUpdate):
    db_day_off = db.query(models.DayOff).filter(models.DayOff.id == days_off.id).first()
    if not db_day_off:
        raise HTTPException(404, detail="No day off with id {}".format(days_off.id))
    db_day_off.start_date = days_off.start_date
    db_day_off.end_date = days_off.end_date
    db_day_off.reason = days_off.reason
    db_day_off.type = days_off.type
    db.commit()
    db.refresh(db_day_off)
    return db_day_off.day_off_get


def delete_days_off(db: Session, id: int):
    db_day_off = db.query(models.DayOff).filter(models.DayOff.id == id).first()
    if not db_day_off:
        raise HTTPException(404, detail="No day off with id {}".format(id))
    db.delete(db_day_off)
    db.commit()
    return db_day_off.day_off_get