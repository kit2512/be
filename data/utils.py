import json
from datetime import datetime
from email.message import EmailMessage

from sqlalchemy.orm import Session

from data import crud

import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from requests import HTTPError


creds = Credentials.from_service_account_file('data/credentials.json')
delegated_credentials = creds.with_subject('dannamdinh49@gmail.com')
service = build('gmail', 'v1', credentials=delegated_credentials)


async def send_salary_emails(db: Session, start_date: datetime.date, end_date: datetime.date):
    db_employees = crud.get_employees(db)
    for emp in db_employees:
        workdays = crud.get_emp_work_hour(db, emp.id, start_date, end_date)
        if workdays.paid_amount > 0:
            send_salary_email(emp.user.email, workdays)


def send_salary_email(db: Session, employee_id: int, start_date: datetime.date, end_date: datetime.date):
    db_employee = crud.get_employee(db, employee_id)
    if not db_employee:
        raise Exception('Employee not found')
    email = db_employee.user.email
    workdays = crud.get_emp_work_hour(db, employee_id, start_date, end_date)
    msg = EmailMessage()
    msg.set_content(f'You have been paid {workdays.paid_amount} for working from {workdays.start_date} to {workdays.end_date}')
    msg['subject'] = 'Payslip from Smart Attendance System'
    msg['to'] = email
    msg['from'] = 'dannamdinh49@gmail.com'
    create_message = {'message': {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}}
    try:
        message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(F'sent message to {message} Message Id: {message["id"]}')
    except HTTPError as error:
        print(F'An error occurred: {error}')
        message = None


# def send_days_off_email(db: Session, day_off: schemas.DayOffGet):
#     db_emp = crud.get_employee(db, day_off.employee_id)
#     msg = EmailMessage()
#     msg.set_content(f'Your day off request from {day_off.start_date} to {day_off.end_date} has been approved')
#     msg['Subject'] = 'Day off request approved'
#     msg['From'] = 'dannamdin49@gmail.com'
#     msg['To'] = db_emp.user.email
#     mail_server.send_message(msg)
