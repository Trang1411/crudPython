import glob

import requests
import schedule
import time
import json
import os
import calendar

from datetime import datetime


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

    with open(json_file, "r") as file:
        data_file_json = json.load(file)

    # print("======================>> ", type(data_file_json))
    # print("======================>> ", data_file_json)
    # Lấy dữ liệu của "_" trong mỗi json và lưu vào globalVal
    config_file_json = data_file_json["config_file"]

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
                    print("The file exists.")
                else:
                    print("The file does not exist.")
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

    print("response_data ====== ", response_data)
    #     Thực hiện lấy response trả về "_" và lưu vào globalVal
    if _pr is not None:
        for k, v in _pr.items():
            # chuyển đổi v thành path để lấy giá trị trong response
            path = v.replace("$", "")
            print("v_path  ======", path)
            value = get_value_by_path(response_data, path)
            if value is not None:
                globalVal[k] = value
            else:
                globalVal[k] = globalVal.get(path)

        # Ghi dữ liệu của "_" vào file myVal.txt
        writeFile("myVal.txt", globalVal)
    print("SUCCESS!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    return


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


def checkServiceNameExists(service_name):
    old = readFileScheduleData()
    # nếu itemNew trùng với data trong file scheduleData thì thông báo cho người dùng
    print("service_name check ====== ", service_name)
    for item in old:
        print("service_name of item in old ====== ", item["service_name"])
        # if service_name == item["service_name"]:
        # old.remove(item["service_name"])
        # return False
    return True


def executeFile():
    dataFile = readFileScheduleData()
    # print("type of file scheduleData ============= ", type(dataFile))
    # print("check file scheduleData ============= ", dataFile)
    for item in dataFile:

        print("check implementFile - file_name ::::: ", item["service_name"])
        data = item["time_set"]
        for key in data.keys():
            if key == "EVT":
                evt(data["EVT"], item["service_name"])

            if key == "EVD":
                evd(data["EVD"], item["service_name"])

            if key == "EVM":
                evm(data["EVM"], item["service_name"])

        continue


# So sánh thời gian hiện tại với thời gian đã set
def isHHmmss(time_set_value):
    # Lấy thời gian hiện tại
    now = datetime.now()

    # chuyển str time_set_value thành thời gian
    time_set_value = datetime.strptime(time_set_value, "%H:%M:%S")

    # So sánh với giờ time_set_value
    if now.hour == time_set_value.hour and now.minute == time_set_value.minute and now.second == time_set_value.second:
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
def evd(time_list, file_name):
    print("time_list evd ============== ", time_list)
    for schedule_time in time_list:
        # kiểm tra thời điểm hiện tại có phải đến giờ thực thi hay không, nếu True thì thực thi
        check = isHHmmss(schedule_time)
        if check is True:
            schedule.every().day.at(schedule_time).do(lambda: read_json_file(file_name))
    while True:
        schedule.run_pending()
        time.sleep(1)


def evt(time_list, file_name):

    for schedule_time in time_list:
        print("check file_name in function ev... ", file_name, " ------------ schedule_time --------------", schedule_time)
        schedule.every(int(schedule_time)).seconds.do(lambda: read_json_file(file_name))

    while True:
        schedule.run_pending()
        time.sleep(1)


def evm(time_list, file_name):
    # Lấy tháng hiện tại
    month = datetime.today().month
    # Lấy số ngày trong tháng hiện tại
    days_in_month = calendar.monthrange(month, 1)[0]
    print("010101010101010101010 ", time_list)

    for item in time_list:
        day = item["day"]
        hour = item["hour"]
        checkDayHHmmss = isDayHHmmss(day, hour)

        if checkDayHHmmss is True:
            if int(day) > days_in_month:
                day = days_in_month
            else:
                day = day
            schedule.every().month.day(day).at(hour).do(lambda: read_json_file(file_name))
    # while True:
    schedule.run_pending()
    time.sleep(1)
