import glob

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

# Hàm schedule.run_pending() kiểm tra xem thời gian thực hiện của tác vụ đầu tiên trong hàng đợi đã đến hay chưa.
    # Nếu đến rôi thì thực hiện tác vụ và xóa nó khỏi hàng đợi
def evd(time_list, read_json_file):
    global time
    for time in time_list:
        schedule.every().day.at(time).do(read_json_file)
    while True:
        schedule.run_pending()
        time.sleep(1)


def evt(time_list, read_json_file):
    global time
    for time in time_list:
        schedule.every(time).minutes.do(read_json_file)
    while True:
        schedule.run_pending()
        time.sleep(1)