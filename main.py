import csv
import json
import os

import requests

def main():
    globalVal = {}

    # đọc file json
    with open("tempJson.json", "r", encoding='utf-8') as file:
        data = json.load(file)

    # Lấy dữ liệu của "_" trong mỗi json và lưu vào `globalVal`
    for item in data:
        _pr = item.get("_")
        for k, v in _pr.items():
            path = v.replace("$", "")
            globalVal[k] = item.get(path)

    # Thực hiện các yêu cầu HTTP
    for item in data:
        headers = item.get("headers")
        url = item.get("url")
        method = item.get("method")
        response_data = None

        # Gọi hàm tương ứng để xử lý từng phương thức HTTP
        if method == "POST":
            response_data = _post(url, headers, item.get("body"))
        elif method == "GET":
            response_data = _get(url, headers)
        elif method == "PUT":
            response_data = _put(url, headers, item.get("body"))
        elif method == "UPLOAD_FILE":
            response_data = _upload_file(url, headers, item.get("body"))

        # Lấy dữ liệu từ response và lưu vào `globalVal`
        for k, v in _pr.items():
            path = v.replace("$", "")
            globalVal[k] = response_data.get(path)

        # Ghi dữ liệu của "_" vào file myVal.csv
        with open("myVal.csv", "w") as saveV:
            writer = csv.writer(saveV, delimiter=",")
            for key, value in globalVal.items():
                writer.writerow([key, value])

def _post(url, headers, body):
    response = requests.post(url, headers=headers, data=body)
    response.raise_for_status()
    return response.json()


def _get(url, headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def _put(url, headers, body):
    response = requests.put(url, headers=headers, data=body)
    response.raise_for_status()
    return response.json()


def _upload_file(url, headers, body):
    response = requests.post(url, headers=headers, files=body)
    response.raise_for_status()
    return response.json()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
