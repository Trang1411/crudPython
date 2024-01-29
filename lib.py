import asyncio
import datetime
import glob
import json
import os
import re
import shutil
import time
from functools import partial
from json import JSONDecodeError

import requests
import schedule
from flask import jsonify
from telegram import Bot


# import tracemalloc
# tracemalloc.start()

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
        print(f"Lỗi http khi thực thi   _post ========= {response.status_code}: {response.text}")
        return {"status": response.status_code, "url": response.url, "time": datetime.datetime.now(),
                "_error": error, "elapsed_time": response.elapsed}
    return {"response_data": response.json(), "elapsed_time": response.elapsed}


def _get(url, headers, body):
    global response
    try:
        response = requests.get(url, headers=headers, data=body)
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        return {"status": response.status_code, "url": response.url, "time": datetime.datetime.now(),
                "_error": error, "elapsed_time": response.elapsed}
    return {"response_data": response.json(), "elapsed_time": response.elapsed}


def _put(url, headers, body):
    global response
    try:
        response = requests.put(url, headers=headers, data=body)
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        return {"status": response.status_code, "url": response.url, "time": datetime.datetime.now(),
                "_error": error, "elapsed_time": response.elapsed}
    return {"response_data": response.json(), "elapsed_time": response.elapsed}


def _upload_file(url, headers, body, files):
    global response
    try:
        response = requests.post(url, headers=headers, files=files, data=body)
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        print(f"Lỗi http khi thực thi  _upload_file ====== {response.status_code}: {response.text}")
        return {"status": response.status_code, "url": response.url, "time": datetime.datetime.now(),
                "_error": error, "elapsed_time": response.elapsed}
    return {"response_data": response.json(), "elapsed_time": response.elapsed}


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


def check_response(response_data, method, url, body, service_name):
    err = {}
    # kiem tra trang thai neu khac 200
    # kiem tra thoi gian tra ve neu >10s thi gui canh bao warning
    # build message
    # gui len nhom telegram
    time_r = response_data.get("elapsed_time")
    total_time = time_r.total_seconds()
    print("response_data.get(elapsed_time) ==== ", total_time)
    if "_error" in response_data:
        message_e = f'{response_data.get("_error")} \n Body: {body}'
        print(f" =============> message tại check_response: {message_e}")
        err = {"message": message_e, "type": "error"}
    if int(total_time) > 10:
        message_w = (f"⚠️⚠️⚠️ **WARNING!!!** \n Dịch vụ ** {service_name} ** \n"
                     f" Thực hiện {method} đến url: {url} có response_tine là"
                     f" {total_time}")
        err = {"message": message_w, "type": "warning"}
    # print("err in check_response ============== ", err)
    return err


def read_json_file(service_name, day_run):
    global file_path, check_resp, mess, t_u, api_key, chat_id, total_time
    try:
        time_start = time.time()
        # print(f"day run ===== {day_run} và json_file ==== {service_name}")
        if day_run == datetime.date.today().day or day_run == 0:

            globalVal = {}
            # Đọc file json
            path = os.path.join("botData", service_name, "config.json")
            with open(path, "r") as file:
                data_file_json = json.load(file)

            # lấy thông tin gửi lên telegram
            api_key = data_file_json.get("token_telegram")
            chat_id = data_file_json.get("chat_id")
            success_msg = data_file_json.get("success_msg")
            # print(f" ============ is_send_success ============ > {success_msg}")

            tag_users = data_file_json.get("user_telegram")
            # print(f" tên đối tượng nhận thông báo ================> {tag_users}")
            t_u = ""  # gắn vào mess để tag tên trong noti
            for user in tag_users:
                t_u += "@" + user + " "
            print(f" tên các user đc tag trong noti là {t_u}")

            config_file = data_file_json["config_file"]
            dem = 0
            for config_file_json in config_file:

                # Lấy dữ liệu của mỗi mục trong json
                body = config_file_json.get("body")
                # print(f"================ body của file {service_name} là {body} ====================")
                headers = config_file_json.get("headers")
                url = config_file_json.get("url")
                _pr = config_file_json.get("_")
                method = config_file_json.get("method")
                condition_cf = config_file_json.get("condition")
                print(f"condition ================ {condition_cf}")
                print(f"type ================ {type(condition_cf)}")
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
                            # print("file_path:::::::::::::", file_path)
                            #     Kiểm tra file có tồn tại hay không?
                            if file_path is None:
                                # print("The file in json_file does not exists.")
                                raise ValueError(f"File {str(v)} không tồn tại.")

                # Thực hiện request
                if method == "POST":
                    response_data = _post(url, headers, body)
                    # print(f" file {service_name}, phương thức POST ===== và kết quả là {response_data}")
                if method == "GET":
                    response_data = _get(url, headers, body)
                    # print(f" file {service_name} và phương thức GET ===== kết quả là {response_data}")
                if method == "PUT":
                    response_data = _put(url, headers, body)
                    # print(f" file {service_name} và phương thức PUT ===== kết quả là {response_data}")
                if method == "UPLOAD_FILE":
                    with open(file_path, "rb") as image_file:
                        response_data = _upload_file(url, headers, body, {"file": image_file})
                dem += 1

                print(f" response_data =================== > {response_data}")

                the_end_time = time.time()
                total_time = the_end_time - time_start

                #     Thực hiện lấy response trả về "_" và lưu vào globalVal
                if _pr is not None:
                    for k, v in _pr.items():
                        # chuyển đổi v thành path để lấy giá trị trong response
                        path = v.replace("$", "")
                        # print("v_path  ======", path)
                        value = get_value_by_path(response_data.get("response_data"), path)
                        if value is not None:
                            # Lấy danh sách các điều kiện để kiểm tra với response của mỗi request
                            globalVal[k] = value
                        else:
                            globalVal[k] = globalVal.get(path)
                            # check response_data, nếu có message thì gửi thông báo lên telegram theo type (error/ warning)
                            check_resp = check_response(response_data, method, url, body, service_name)
                            if "message" in check_resp and check_resp.get("type") == "error":
                                # print(f' message báo lỗi ======= {check_resp.get("message")}'
                                #       f"\n Thực hiện {method} đến url: {url}"
                                #       f"\n Body: {body}"
                                #       )
                                # gửi lên telegram
                                raise ValueError(check_resp.get("message"))
                            if "message" in check_resp and check_resp.get("type") == "warning":
                                # gửi lên telegram
                                mess_warning = check_resp.get("message")
                                # print(f' message cảnh báo ======= {mess_warning}')
                                # asyncio.run(send_mess_format_text(api_key, chat_id, "BOT SYSTEM", mess_warning))
                    print(f"global_val TYPE================ {type(globalVal)}")
                    if condition_cf is not None:
                        mess_condition = condition_text(condition_cf, response_data, globalVal, service_name, t_u)
                        if mess_condition is not None:
                            asyncio.run(send_mess_format_text(api_key, chat_id, "BOT SYSTEM", mess_condition))

                    # Ghi dữ liệu của "_" vào file myVal.txt
                    writeFile("myVal.txt", globalVal)

            # check_send = data_file_json["config_file"]["is_send_success"]
            # print(f"========================== check send ==========================> {check_send}")
            mess = f"✅✅✅ SUCCESS!!! \n Số lượng request: {dem} \n Thời gian chạy dịch vụ **{service_name}** là {total_time} giây."
            print(f"========== \n Kết thúc và không gửi thông báo \n ============")
            if success_msg != "true":
                asyncio.run(send_mess_format_text(api_key, chat_id, "BOT SYSTEM", mess))

    except ValueError as err:
        message = f"❌❌❌ ERROR \n Dịch vụ {service_name} \n {err}. \n {t_u} vui lòng kiểm tra."
        print("lỗi đâyyyyy (ValueError): ", message)
        asyncio.run(send_mess_format_text(api_key, chat_id, "BOT SYSTEM", message))

    except Exception as err:
        message = f"❌❌❌ ERROR \n Dịch vụ {service_name} \n {err}. \n {t_u} vui lòng kiểm tra."
        print("========== > Exception: ", message)  # , message)
        asyncio.run(send_mess_format_text(api_key, chat_id, "BOT SYSTEM", message))

    return


async def send_mess_format_text(api_key, _chat_id, _from, _mess="Hello world", _file=None):
    # api_key = "5579530637:AAHiJONsPHZ0bTsiHANWBrfqvE4QoRv0BlM"
    bot = Bot(token=api_key)
    if _file:
        try:
            document = open(_file, "rb")
            await bot.send_document(chat_id=_chat_id,
                                    filename=_file,
                                    document=document,
                                    caption=_mess)
        except Exception as e:
            print(e)
    else:
        await bot.send_message(chat_id=_chat_id,
                               text=f"From [{_from}]\n{_mess}")


def check_type_condition(value_condition):
    is_str = isinstance(value_condition, str)
    if is_str is True:
        return "str"
    else:
        return "dict"


def condition_text(condition, response_data, globalVal, service_name, user):
    global message, variable, operator, value_condition
    # tách condition thành các thành phần biến | toán tử (nếu có) | giá trị so sánh của biến

    for cond in condition:
        conds = cond.split("|")
        variable = conds[0]
        variable = variable[1:]
        if len(conds) == 3:
            operator = conds[1]
        else:
            value_condition = conds[-1]
            value_condition = value_condition.replace("%", "")
        print(f" tên biến là {variable}, với giá trị so sánh là {value_condition}")

        # lấy biến và giá trị tương ứng trong điều kiện so sánh với response_data
        # kiểm tra nếu không có biến đó trong response_data hoặc không có trong "_" (globalVal)=> báo lỗi
        if variable not in response_data and variable not in globalVal.keys():
            message = (f"❌❌❌ ERROR (không đạt điều kiện)\n Dịch vụ {service_name} \n "
                       f"Kết quả trả về không chứa {variable}. \n {user} vui lòng kiểm tra.")
            print(f" ===================== nội dung thông báo: không đúng với đoạn text điều kiện: {message}")
        # nếu có biến trong response hoặc "_" (globalVal) thì so sánh giá trị trả về với điều kiện
        if variable in response_data or variable in globalVal:
            print(f"============ kết quả trả về có {variable}")
            # nếu chứa toán tử
            # if operator is not None:
            #     response_data["object"][variable]  value_condition
            if value_condition not in globalVal[variable]:
                message = (f"❌❌❌ ERROR (không đạt điều kiện)\n Dịch vụ {service_name} \n "
                           f"Kết quả trả về giá trị của {variable} không chứa {value_condition}. \n {user} vui lòng kiểm tra.")
        return message


def condition_json(value_condition, response_data, service_name, user):
    k_c = list(value_condition.keys())[0]
    v_c = value_condition[k_c]
    k_c = k_c[1:]
    print(f"================ tên biến trong file config là =============== > {k_c}")
    for key in response_data.keys():
        if k_c == key:  # có tồn tại biến đó trong config
            if response_data[key] != v_c:
                message = (f"❌❌❌ ERROR (không đạt điều kiện)\n Dịch vụ {service_name} \n "
                           f"Kết quả trả về không đúng {k_c} : {response_data[k_c]} với điều kiện là {k_c}: {v_c} \n {user} vui lòng kiểm tra.")
                return message
        # kiểm tra có tồn tại trong danh sách key của value của config không (value là json,
        # kiểm tra có tồn tại key điều kiện trong json đó không)
        else:
            if key.k_c not in response_data:
                message = (f"❌❌❌ ERROR (không đạt điều kiện)\n Dịch vụ {service_name} \n "
                           f"Kết quả trả về không tồn tại *{k_c}* \n {user} vui lòng kiểm tra.")
                return message
            else:
                if response_data[key][k_c] != v_c:
                    message = (f"❌❌❌ ERROR (không đạt điều kiện)\n Dịch vụ {service_name} \n "
                               f"Kết quả trả về không đúng {k_c} : {response_data[k_c]} với điều kiện là {k_c}: {v_c} \n {user} vui lòng kiểm tra.")
                    return message


def readFile(path):
    with open(path, "r") as rf:
        data = json.load(rf)
    return data


def writeFile(filename, dataSave):
    with open(filename, "w") as saveData:
        json.dump(dataSave, saveData, indent=4)


def updateFile(filename, dataSave):
    with open(filename, 'r') as f:
        data = json.load(f)

    data.update(dataSave)
    # chuyển dữ liệu thành chuỗi json
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


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


def delete_service_before_update(service_name):
    print(f"11111111111 {service_name}")
    path = os.path.join("botData", service_name)
    print(os.path.exists(path))
    if os.path.exists(path):
        print(f"có tồn tại dịch vụ {service_name}")
        # tạo đường dẫn chuẩn cho dịch vụ cần xóa

        shutil.rmtree(path)
        print(f" ============= xóa dịch vụ {service_name} cũ để lưu thông tin vừa cập nhật nè =========== ")
