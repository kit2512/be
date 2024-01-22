from datetime import datetime

from sqlalchemy.orm import Session

from data import crud, schemas


async def send_salary_emails(db: Session, start_date: datetime.date, end_date: datetime.date):
    db_employees = crud.get_employees(db)
    for emp in db_employees:
        workdays = crud.get_emp_work_hour(db, emp.id, start_date, end_date)
        if workdays.paid_amount > 0:
            send_salary_email(emp.user.email, workdays)


def send_salary_email(email: str, workdays: schemas.WorkDaysResponse):
    pass


def send_days_off_email(db: Session, day_off: schemas.DayOffGet):
    db_emp = crud.get_employee(db, day_off.employee_id)
    pass



