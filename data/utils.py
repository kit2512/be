import asyncio
import numbers
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from data import crud

GMAIL_EMAIL='dannamdinh49@gmail.com'
GMAIL_PASSWORD='xikh nhhp gzzp ygjy'
html_file = open("data/salary_email_content.html", "r")
salary_email_content = html_file.read()


def send_salary_email(db: Session, employee_id: int, start_date: datetime.date, end_date: datetime.date):
    db_employee = crud.get_employee(db, employee_id)
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    workdays = crud.get_emp_work_hour(db, employee_id, start_date, end_date)
    email_content = salary_email_content.format(
        start_date,
        end_date,
        db_employee.user.full_name,
        workdays.total_hours,
        db_employee.salary,
        workdays.total_hours * db_employee.salary
    )
    send_email(db_employee.user.email, "Salary report", email_content)


def send_email(to_email, subject, content):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(GMAIL_EMAIL, to_email, text)
    server.quit()