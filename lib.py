import glob
from datetime import datetime

import requests
import schedule
import time

from flask import json


def _post(url, headers, body):
    response = requests.post(url, headers=headers, data=body)
    response.raise_for_status()
    return response.json()


def _get(url, headers, body):
    response = requests.get(url, headers=headers, data=body)
    response.raise_for_status()
    return response.json()


def _put(url, headers, body):
    response = requests.put(url, headers=headers, data=body)
    response.raise_for_status()
    return response.json()


def _upload_file(url, headers, body, files):
    response = requests.post(url, headers=headers, files=files, data=body)
    response.raise_for_status()
    return response.json()

def get_value_by_path(json_obj, path):
    keys = path.split('.')
    current_obj = json_obj

    try:
        for key in keys:
            if isinstance(current_obj, list):
                key = int(key)
            current_obj = current_obj[key]
        return current_obj
    except (TypeError, IndexError, KeyError):
        return None

def get_path(filename):
    files = glob.glob(f'*{filename}*')
    if files:
        return files[0]
    else:
        return None

# Hàm schedule.run_pending() kiểm tra xem thời gian thực hiện của tác vụ đầu tiên trong hàng đợi đã đến hay chưa.
# Nếu đến rôi thì thực hiện tác vụ và xóa nó khỏi hàng đợi
def evd(time_list, read_json_file):
    for schedule_time in time_list:
        schedule.every().day.at(schedule_time).do(lambda: read_json_file("file_name"))
    while True:
        schedule.run_pending()
        time.sleep(1)


def evt(time_list, read_json_file):
    for schedule_time in time_list:
        schedule.every(int(schedule_time)).seconds.do(lambda: read_json_file("file_name"))
    while True:
        schedule.run_pending()
        time.sleep(1)

def evm (time_list, read_json_file):
    global day_of_month
    for schedule_time in time_list:
        # Kiểm tra xem ngày của tháng có phải là 29 hoặc 30 hay không.

        if datetime.datetime.now().day == 29 or datetime.datetime.now().day == 30:
            if datetime.datetime.now().month % 4 == 0:
            # Thay đổi ngày của tháng thành 28 hoặc 29.
                schedule_time = 28
            else:
                schedule_time = 29
        # Tạo công việc.
        schedule.every().month(day_of_month).do(lambda: read_json_file("file_name"))

def readFileScheduleData():
    with open("scheduleData.json", "r") as rf:
        fileScheduleData = json.load(rf)
    return fileScheduleData


def writeFileScheduleData(dataSave):
    with open("scheduleData.json", "w") as saveData:
        json.dump(dataSave, saveData)

def writeFile(filename, dataSave):
    with open(filename, "w") as saveData:
        json.dump(dataSave, saveData)