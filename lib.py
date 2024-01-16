import datetime
import glob
import json
import os
import re
from functools import partial

import requests
import schedule


def check_response(response_data, method, url, body, service_name):
    err = {}
    # kiem tra trang thai neu khac 200
    # kiem tra thoi gian tra ve neu >10s thi gui canh bao warning
    # build message
    # gui len nhom telegram
    if "_error" in response_data:
        message = f'Dịch vụ {service_name} thực hiện {method} với url: {url} \n, body: {body} \n lỗi {response_data.get("_error")}'
        err = {"message": message, "type": "error"}
    if "_error" not in response_data and response_data.get("elapsed_time") > 10:
        message = f"warning: Dịch vụ {service_name} có response_tine là {response_data.get('elapsed_time')}"
        err = {"message": message, "type": "warning"}
    return err


def _post(url, headers, body):
    # print("URL POST", url)
    # print("headers POST", headers)
    # print("Body POST", body)
    global response
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        # print(error)
        # print("Ket qua ", response.text)
        return {"status": response.status_code, "url": response.url, "time": datetime.datetime.now(),
                "_error": error, "elapsed_time": response.elapsed}
    return {"response_data": response.json(), "elapsed_time": response.elapsed}


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


def get_path(path, filename):
    files = glob.glob(f'{path}/*{filename}*')
    if files:
        return files[0]
    else:
        return None


def read_json_file(service_name, day_run):
    try:
        print(f"day run ===== {day_run} và json_file ==== {service_name}")
        if day_run == datetime.date.today().day or day_run == 0:
            global file_path, check_resp
            globalVal = {}
            # Đọc file json
            # print("0000000000000", json_file)
            path = os.path.join("botData", service_name, "config.json")
            with open(path, "r") as file:
                data_file_json = json.load(file)

            # print("======================>> ", type(data_file_json))
            # print("======================>> ", data_file_json)
            # Lấy dữ liệu của "_" trong mỗi json và lưu vào globalVal
            config_file = data_file_json["config_file"]
            for config_file_json in config_file:

                # Lấy dữ liệu của mỗi mục trong json
                body = config_file_json.get("body")
                print(f"================ body của file {service_name} là {body} ====================")
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
                            file_path = get_path(os.path.join("botData", service_name), str(v))
                            print("file_path:::::::::::::", file_path)
                            #     Kiểm tra file có tồn tại hay không?
                            if file_path is None:
                                print("The file in json_file does not exists.")
                                raise ValueError(
                                    f" Loi o dich vu {service_name} khi đọc file{str(v)} ==> The file in json_file does not exists.")
                # Thực hiện request
                if method == "POST":
                    response_data = _post(url, headers, body)
                    print(f" file {service_name}, phương thức POST ===== và kết quả là {response_data}")
                if method == "GET":
                    response_data = _get(url, headers, body)
                    print(f" file {service_name} và phương thức GET ===== kết quả là {response_data}")
                if method == "PUT":
                    response_data = _put(url, headers, body)
                    print(f" file {service_name} và phương thức PUT ===== kết quả là {response_data}")
                if method == "UPLOAD_FILE":
                    with open(file_path, "rb") as image_file:
                        response_data = _upload_file(url, headers, body, {"file": image_file})
                        print(f" file {service_name} phương thức UPLOAD_FILE ===== và kết quả là {response_data}")

                # check kết quả response_data, nếu có key = _error thì gửi lên telegram với {url, body, @user}
                check_resp = check_response(response_data, method, url, body, service_name)
                if "message" in check_resp:
                    raise ValueError(f"Dịch vụ {service_name} thực thi thành công!!!")
                # gửi lên telegram
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
                print(f"SUCCESS!!! - ", f"Thời gian chạy {service_name} là  ====== {datetime.datetime.now()}")
    except ValueError as err:
        print("lôi day", err)
    return check_resp


def readFile(path):
    with open(path, "r") as rf:
        data = json.load(rf)
    return data


def writeFile(filename, dataSave):
    with open(filename, "w") as saveData:
        json.dump(dataSave, saveData, indent=4)


def is_time(key):
    parts = key.split(":")
    if len(parts) == 3 and all(part.isdigit() for part in parts) and re.match(r"^\d{2}:\d{2}:\d{2}$", key) is not None:
        return True
    return False


# Hàm schedule.run_pending() kiểm tra xem thời gian thực hiện của tác vụ đầu tiên trong hàng đợi đã đến hay chưa.
# Nếu đến rôi thì thực hiện tác vụ và xóa nó khỏi hàng đợi
def evd(time_run, service_name):
    # chuyển str time_set_value thành thời gian
    times = datetime.datetime.strptime(time_run, "%H:%M:%S")
    hms = times.strftime("%H:%M:%S")

    print(f" thời gian thực thi là {hms}")
    print(f"EVD ============== ", service_name)
    job_with_params = partial(read_json_file, service_name, 0)
    job = schedule.every().day.at(hms).do(job_with_params)
    # print(f"Thời gian chạy {file_name} là  ============== ", datetime.now())
    print(f"Thời gian lần thực thi trước đó của file {service_name} là: {job.last_run}")

    # while True:
    #     for file_name in file_names:
    #         schedule.run_pending()
    #         time.sleep(1)


def evt(time_run, service_name):
    print(f"EVT ============== ", service_name)
    job_with_params = partial(read_json_file, service_name, 0)
    schedule.every(int(time_run)).seconds.do(job_with_params)
    # print(f"Thời gian chạy {file_name} là  ============== ", datetime.now())
    # print(f"Thời gian lần thực thi trước đó của file {file_name} là: {job.last_run}")


def evm(time_run, service_name):
    day_time_run = int(time_run[:2])
    hours = time_run[3:]
    # chuyển str time_set_value thành thời gian
    hour = datetime.datetime.strptime(hours, "%H:%M:%S")
    hms = hour.strftime("%H:%M:%S")
    print(f" time_run =========== {time_run} bao gồm ngày {day_time_run} vào lúc {hms}")
    job_with_params = partial(read_json_file, service_name, day_time_run)
    schedule.every().day.at(hms).do(job_with_params)  # lên lịch thực thi dịch vụ
    print("lên lịch thành công")
    # print(f"Thời gian chạy {file_name} là  ============== ", datetime.now())
    # print(f"Thời gian lần thực thi trước đó của file {file_name} là: {job.last_run}")


def checkhhmmss(str_value):
    parts = str_value.split(':')
    if len(parts) != 3:
        return False
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2])
        return 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59
    except ValueError:
        return False
