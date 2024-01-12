import calendar
import glob
import json
import os
import re
import time
from datetime import datetime
from functools import partial

import requests
import schedule


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


def read_json_file(json_file):
    global file_path
    globalVal = {}
    # Đọc file json
    # print("0000000000000", json_file)
    path = os.path.join("botData", json_file)
    with open(path, "r") as file:
        data_file_json = json.load(file)

    # print("======================>> ", type(data_file_json))
    # print("======================>> ", data_file_json)
    # Lấy dữ liệu của "_" trong mỗi json và lưu vào globalVal
    config_file = data_file_json["config_file"]
    for config_file_json in config_file:

        # Lấy dữ liệu của mỗi mục trong json
        body = config_file_json.get("body")
        headers = config_file_json.get("headers")
        url = config_file_json.get("url")
        _pr = config_file_json.get("_")
        method = config_file_json.get("method")
        response_data = {}

        # check body của mỗi item để chuẩn bị request
        if body is not None:
            for k, v in body.items():
                if "$" in str(v):
                    v = v.replace("$", "")
                    body[k] = globalVal.get(v)
                # lấy file_path của _file và check exists
                if k == "_file":
                    file_path = get_path(str(v))
                    # print("file_path:::::::::::::", file_path)
                    #     Kiểm tra file có tồn tại hay không?
                    if os.path.exists(file_path):
                        print("The file in json_file exists.")
                    else:
                        print("The file in json_file does not exists.")
        # Thực hiện request
        if method == "POST":
            response_data = _post(url, headers, body)
        if method == "GET":
            response_data = _get(url, headers, body)
        if method == "PUT":
            response_data = _put(url, headers, body)
        if method == "UPLOAD_FILE":
            with open(file_path, "rb") as image_file:
                response_data = _upload_file(url, headers, body, {"file": image_file})

        # print("response_data ====== ", response_data)
        #     Thực hiện lấy response trả về "_" và lưu vào globalVal
        if _pr is not None:
            for k, v in _pr.items():
                # chuyển đổi v thành path để lấy giá trị trong response
                path = v.replace("$", "")
                # print("v_path  ======", path)
                value = get_value_by_path(response_data, path)
                if value is not None:
                    globalVal[k] = value
                else:
                    globalVal[k] = globalVal.get(path)

            # Ghi dữ liệu của "_" vào file myVal.txt
            writeFile("myVal.txt", globalVal)
        print()
        print("SUCCESS!!! - ", f"Thời gian chạy {json_file} là  ====================== ", datetime.now())
        print()
    return


def readFileScheduleData():
    with open("scheduleData.json", "r") as rf:
        fileScheduleData = json.load(rf)
    return fileScheduleData


def writeFileScheduleData(dataSave):
    with open("scheduleData.json", "w") as saveData:
        json.dump(dataSave, saveData, indent=4)


def writeFile(filename, dataSave):
    with open(filename, "w") as saveData:
        json.dump(dataSave, saveData, indent=4)


def executeFile():
    dataFile = readFileScheduleData()
    # print("type of file scheduleData ============= ", type(dataFile))
    # print("check file scheduleData ============= ", dataFile)

    for key in dataFile.keys():
        # Kiểm tra chuỗi có đúng định dạng hh:mm:ss hay không
        check = is_time(key)
        # print(f"check format hh:mm:ss của {key} là ::: ", check)
        if len(key) == 8 and check is True:
            evd(key, dataFile[key])
        elif "_" in key:
            evm(key, dataFile[key])
        else:
            evt(key, dataFile[key])
    while True:
        schedule.run_pending()
        time.sleep(1)

def is_time(key):
    parts = key.split(":")
    if len(parts) == 3 and all(part.isdigit() for part in parts) and re.match(r"^\d{2}:\d{2}:\d{2}$", key) is not None:
        return True
    return False


# So sánh thời gian hiện tại với thời gian đã set
def isHHmmss(time_set_value):
    # Lấy thời gian hiện tại
    now = datetime.now()
    # chuyển str time_set_value thành thời gian
    time_set_value = datetime.strptime(time_set_value, "%H:%M:%S")
    # So sánh với giờ time_set_value
    if now.hour == time_set_value.hour and now.minute == time_set_value.minute:
        return True
    else:
        return False


def isDayHHmmss(day, hhmmss):
    # Lấy ngày hiện tại và kiểm tra giờ hiện tại
    day_now = datetime.today().day
    hhmmss_check = isHHmmss(hhmmss)
    if int(day) == day_now and hhmmss_check is True:
        return True
    else:
        return False


# Hàm schedule.run_pending() kiểm tra xem thời gian thực hiện của tác vụ đầu tiên trong hàng đợi đã đến hay chưa.
# Nếu đến rôi thì thực hiện tác vụ và xóa nó khỏi hàng đợi
def evd(time_run, file_names):
    check = isHHmmss(time_run)
    if check is True:
        print(f"EVD ============== ", file_names)
        for file_name in file_names:
            job_with_params = partial(read_json_file, file_name)
            # kiểm tra thời điểm hiện tại có phải đến giờ thực thi hay không, nếu True thì thực thi
            job = schedule.every().day.at(time_run).do(job_with_params)
            # print(f"Thời gian chạy {file_name} là  ============== ", datetime.now())
            print(f"Thời gian lần thực thi trước đó của file {file_name} là: {job.last_run}")

    # while True:
    #     for file_name in file_names:
    #         schedule.run_pending()
    #         time.sleep(1)


def evt(time_run, file_names):
    print(f"EVT ============== ", file_names)
    for file_name in file_names:
        job_with_params = partial(read_json_file, file_name)

        schedule.every(int(time_run)).seconds.do(job_with_params)
        # print(f"Thời gian chạy {file_name} là  ============== ", datetime.now())
        # print(f"Thời gian lần thực thi trước đó của file {file_name} là: {job.last_run}")


def evm(time_run, file_names):
    # Lấy tháng hiện tại
    month = datetime.today().month
    #  Lấy năm hiện tại
    year = datetime.today().year
    # Lấy số lượng ngày trong tháng hiện tại
    days_in_month = calendar.monthrange(year, month)[1]
    day = time_run[:2]
    hour = time_run[3:]
    # print(f"====---- day là {day}, hour là {hour} ----====")
    checkDayHHmmss = isDayHHmmss(day, hour)
    if checkDayHHmmss is True:
        if int(day) > days_in_month:
            day = days_in_month
        else:
            day = day
        print(f"EVM ============== ", file_names)
        for file_name in file_names:
            job_with_params = partial(read_json_file, file_name)
            job = schedule.every().month.day(day).at(hour).do(job_with_params)
            # print(f"Thời gian chạy {file_name} là  ============== ", datetime.now())
            print(f"Thời gian lần thực thi trước đó của file {file_name} là: {job.last_run}")

