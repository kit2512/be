import datetime
import json

import requests

create_emp_url = 'http://0.0.0.0/employee/create'
create_card_url = 'http://0.0.0.0/card/create'
create_checkin_url = 'http://0.0.0.0/checkin/create'

try:
    for x in range(2, 10):
        print('-------------------')
        create_employee_data = {
            "first_name": "Employee {}".format(x),
            "last_name": "Demo",
            "username": "employee{}".format(x),
            "password": "@Hung12345",
            "role": "employee" if x % 10 else "manager",
            "allowed_rooms": [1] + ([2] if x % 10 else []),
            "salary": 1000000 if x % 10 else 2000000,
            "email": "employee{}@gmail.com".format(x),
        }
        print(json.dumps(create_employee_data))
        response = requests.post(create_emp_url, json=create_employee_data)
        if response.status_code != 200:
            print("Failed to create employee {}".format(x))
            print(response.reason)
        else:
            print("Created employee {} successfully".format(x))
            print(response.json())
            print('EMPLOYEE ID: {}'.format(response.json()['id']))
            create_card_data = {
                "id": "123456789{}".format(x),
                "date_created": datetime.datetime.now().isoformat(),
                "employee_id": response.json()['id']
            }
            card_response = requests.post(create_card_url, json=create_card_data)
            if card_response.status_code != 200:
                print("Failed to create card for employee {}".format(x))
                print(card_response.json())
            else:
                for k in range(1, 10):
                    date_created = datetime.datetime(2024, 1, k, 8, 0, 0)
                    create_check_in_data = {
                        "rfid_machine_id": 1,
                        "card_id": card_response.json()['id'],
                        "date_created": date_created.isoformat()
                    }
                    requests.post(create_checkin_url, json=create_check_in_data)
                    date_created = datetime.datetime(2024, 1, k, 17, 0, 0)
                    create_check_in_data = {
                        "rfid_machine_id": 1,
                        "card_id": card_response.json()['id'],
                        "date_created": date_created.isoformat()
                    }
                    requests.post(create_checkin_url, json=create_check_in_data)
                    print("Checkin for employee {} at machine 1".format(x))
except Exception as e:
    print(e)
