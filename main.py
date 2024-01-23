import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from data import database, models, crud, schemas, utils
from data.database import SessionLocal
from data.schemas import UserGet, EmployeeGet, EmployeeCreate, RfidMachine, Room, RfidMachineCreate, \
    CheckinHistoryItemGet, CheckinHistoryItemCreate, RfidCardCreate, RfidCardGet

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="HRM")
origins = [
    "http://localhost",
    "http://localhost:5000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post('/employee/create', response_model=schemas.EmployeeGet)
async def create_employee(new_employee: EmployeeCreate, db: Session = Depends(get_db)):
    user_db = crud.create_employee(db, new_employee)
    return EmployeeGet(
        id=user_db.id,
        user_id=user_db.user_id,
        salary=user_db.salary,
        user=UserGet(
            id=user_db.user_id,
            username=user_db.user.username,
            first_name=user_db.user.first_name,
            last_name=user_db.user.last_name,
            date_created=user_db.user.date_created,
            role=user_db.user.role,
        ),
    )


@app.post('/room/create', response_model=Room)
async def create_room(new_room: schemas.RoomCreate, db: Session = Depends(get_db)):
    if len(new_room.name) == 0:
        raise HTTPException(400, detail='Name must not be empty')
    db_room = crud.create_room(db, new_room)
    if db_room:
        return Room.model_validate(db_room)
    else:
        raise HTTPException(500, "Unknown error")


@app.post('/rfid/create', response_model=RfidMachine)
async def create_rfid_machine(new_rfid_machine: RfidMachineCreate, db: Session = Depends(get_db)):
    db_rfid = crud.create_rfid_machine(db, new_rfid_machine)
    if db_rfid:
        return RfidMachine(
            id=db_rfid.id,
            room_id=db_rfid.room_id,
            name=db_rfid.name
        )
    else:
        raise HTTPException(500, "Unknown error")


@app.delete('/employee/delete')
async def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    crud.delete_employee(db, employee_id)
    return {
        "success": True
    }


@app.patch('/employee/$id/update', response_model=EmployeeGet)
async def update_employee(employee_id: int, new_employee: EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = crud.update_employee(db, employee_id, new_employee)
    return EmployeeGet(
        id=db_employee.id,
        user_id=db_employee.user_id,
        user=UserGet(
            id=db_employee.user_id,
            username=db_employee.user.username,
            first_name=db_employee.user.first_name,
            last_name=db_employee.user.last_name,
            date_created=db_employee.user.date_created,
            role=db_employee.user.role
        ),
    )


@app.post('/checkin/create', response_model=CheckinHistoryItemGet)
async def create_checkin_history(new_checkin_history: CheckinHistoryItemCreate, db: Session = Depends(get_db)):
    db_checkin_item = crud.create_checkin_history_item(db, new_checkin_history)
    if db_checkin_item:
        return convert_checkin_item_to_checkin_item_get(db_checkin_item)
    else:
        raise HTTPException(status_code=500, detail="Unknown error")


@app.post('/employee/assign_rooms', response_model=schemas.EmployeeAssignRooms)
async def employee_assign_rooms(request: schemas.EmployeeAssignRooms, db: Session = Depends(get_db)):
    crud.assign_room_emp(db, request.employee_id, request.room_ids)
    return request


@app.post('/room/assign_employees', response_model=schemas.RoomAssignEmployees)
async def room_assign_employees(request: schemas.RoomAssignEmployees, db: Session = Depends(get_db)):
    crud.assign_emp_room(db, request.room_id, request.employee_ids)
    return request


@app.post('/room/assign_rfids', response_model=dict)
async def room_assign_rfid(room_id: int, rfid_ids: List[int], db: Session = Depends(get_db)):
    crud.assign_rfid_room(db, room_id, rfid_ids)
    return {
        "room_id": room_id,
        "rfids": rfid_ids
    }


@app.get('/employees', response_model=List[EmployeeGet])
async def get_employee_lis(db: Session = Depends(get_db), room_id: int | None = None):
    db_employees = crud.get_employees(db, room_id)
    results: List[EmployeeGet] = []
    for emp in db_employees:
        user = crud.get_user(db, emp.user_id)
        result = EmployeeGet(
            id=emp.id,
            user_id=user.id,
            user=convert_user_to_user_get(user),
            card=convert_cart_to_card_get(emp.card) if emp.card else None,
            salary=emp.salary
        )
        results.append(result)
    return results


@app.get('/rooms', response_model=List[Room])
async def get_rooms(db: Session = Depends(get_db), employee_id: int | None = None):
    db_rooms = crud.get_rooms(db, employee_id)
    return [convert_room_to_room_get(x) for x in db_rooms]


@app.get('/rfids', response_model=List[schemas.RfidMachine])
async def get_rfids(room_id: int | None = None, db: Session = Depends(get_db)):
    db_rfids = crud.get_rfids(db, room_id)
    return [RfidMachine(
        id=x.id,
        name=x.name,
        allow_checkin=x.allow_checkin,
        room_id=x.room_id,
        date_created=x.date_created,
        room=convert_room_to_room_get(x.room)
    ) for x in db_rfids]


@app.post('/card/create', response_model=RfidCardGet)
async def create_card(new_card: RfidCardCreate, db: Session = Depends(get_db)):
    db_card = crud.create_card(db, new_card)
    return convert_cart_to_card_get(db_card)


@app.get('/cards', response_model=List[RfidCardGet])
async def get_cards(is_available: bool = False, db: Session = Depends(get_db)):
    db_cards = crud.get_cards(is_available, db)
    return [convert_cart_to_card_get(x) for x in db_cards]


@app.patch('/cards/assign_employee', response_model=RfidCardGet)
async def assign_card_employee(employee_id: int, card_id: str, db: Session = Depends(get_db)):
    db_card = crud.assign_card(db, card_id, employee_id)
    return convert_cart_to_card_get(db_card)


@app.get('/employee/{id}', response_model=EmployeeGet)
async def get_employee(id: int, db: Session = Depends(get_db)):
    db_employee = crud.get_employee(db, id)
    db_checkin_history = crud.get_checkin_history(db, employee_id=id)
    db_rooms = crud.get_rooms(db, id)
    return EmployeeGet(
        id=db_employee.id,
        user=convert_user_to_user_get(db_employee.user),
        user_id=db_employee.user_id,
        checkin_history=[convert_checkin_item_to_checkin_item_get(x) for x in db_checkin_history],
        allowed_rooms=[convert_room_to_room_get(x) for x in db_rooms],
        card=convert_cart_to_card_get(db_employee.card),
        salary=db_employee.salary
    )


@app.get('/checkin/history', response_model=List[CheckinHistoryItemGet])
async def get_checkin_history(room_id: int | None = None, rfid_id: int | None = None, employee_id: int | None = None,
                              db: Session = Depends(get_db)):
    db_checkins = crud.get_checkin_history(db, room_id, rfid_id, employee_id)
    return [convert_checkin_item_to_checkin_item_get(x) for x in db_checkins]


@app.delete('/room/delete', response_model=schemas.Room)
async def delete_room(id: int, db=Depends(get_db)):
    result = crud.delete_room(db, room_id=id)
    if result:
        return schemas.Room(
            id=result.id,
            name=result.name,
            date_created=result.date_created
        )
    else:
        raise HTTPException(404, "No room with id {}".format(id))


@app.delete('/card/delete/{id}', response_model=RfidCardGet)
async def delete_card(id: str, db=Depends(get_db)):
    result = crud.delete_card(db, id)
    if result:
        return convert_cart_to_card_get(result)
    else:
        raise HTTPException(404, "No card with id {}".format(id))


@app.get('/work_days/{employee_id}', response_model=schemas.WorkDaysResponse)
async def get_work_hour(employee_id: int, start_date: Optional[datetime.date] = None,
                        end_date: Optional[datetime.date] = None, db: Session = Depends(get_db)):
    return crud.get_emp_work_hour(db, employee_id, start_date, end_date)


@app.post('/days_off/create')
async def create_days_off(payload: schemas.DayOffCreate, db=Depends(get_db)):
    return crud.create_days_off(db, payload)


@app.put('/days_off', response_model=schemas.DayOffGet)
async def update_days_off(payload: schemas.DayOffUpdate, db=Depends(get_db)):
    return crud.update_days_off(db, payload)


@app.delete('/days_off/{id}', response_model=schemas.DayOffGet)
async def delete_days_off(id: int, db=Depends(get_db)):
    return crud.delete_days_off(db, id)


@app.post('/employees/{employee_id}/salary_email')
async def send_salary_email(employee_id: int, start_date: datetime.date, end_date: datetime.date, db=Depends(get_db)):
    utils.send_salary_email(db, employee_id, start_date, end_date)


def convert_cart_to_card_get(card: models.RfidCard | None = None):
    if card:
        return RfidCardGet(
            id=card.id,
            employee_id=card.employee_id,
            date_created=card.date_created,
        )


def convert_user_to_user_get(user: models.User):
    return UserGet(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        date_created=user.date_created,
        role=user.role
    )


def convert_room_to_room_get(room: models.Room):
    return Room(name=room.name, id=room.id, date_created=room.date_created, )


def convert_checkin_item_to_checkin_item_get(item: models.CheckinHistoryItem):
    return CheckinHistoryItemGet(
        id=item.id,
        date_created=item.date_created,
        rfid_machine_id=item.rfid_machine_id,
        employee_id=item.employee_id,
        allow_checkin=item.allow_checkin,
        room_id=item.rfid_machine.room_id,
        card_id=item.card.id if item.card else None,
    )