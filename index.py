import json
import os
import array as arr

from flask import Flask, render_template, request, jsonify

from lib import (_get, _put, _post, _upload_file,
                 get_value_by_path, get_path, evd, evt)

app = Flask(__name__)


def read_json_file(json_file):
    global file_path
    globalVal = {}
    # Đọc file json
    with open(json_file, "r", encoding='utf-8') as file:
        data_file_json = json.load(file)

    # print("======================> ", type(data_file_json))
    # print("======================>> ", data_file_json)

    # Lấy dữ liệu của "_" trong mỗi json và lưu vào globalVal
    for item in data_file_json:
        print("=====>>>>>> item: ", item)
        # Lấy dữ liệu của mỗi mục trong json
        body = item.get("body")
        headers = item.get("headers")
        url = item.get("url")
        _pr = item.get("_")
        method = item.get("method")
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
                    print("file_path:::::::::::::", file_path)
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
        with open("myVal.txt", "w") as saveV:
            json.dump(globalVal, saveV)


@app.route('/schedule', methods=['GET', 'POST'])
def form_schedule():
    global data
    if request.method == 'POST':
        config_file_request = request.form.get('config_file')
        time_set_request = request.form.get('time_set_hidden')
        # print("time_set_request type == 111 ==> ", type(time_set_request))
        print("config file type ==============>>>> ", type(config_file_request))

        time_set = json.loads(time_set_request)
        # print(" time_set =================== ", time_set)

        # lưu file config thành file.json
        with open("config_file.json", "w", encoding="utf-8") as c:
            json.dump(config_file_request, c)

        for k in time_set.keys():
            if k == 'EVD' and time_set[k] != []:
                print("==== EVD ======", time_set[k])
                evd(time_set[k], read_json_file("config_file.json"))
            if k == 'EVT' and time_set[k] != []:
                print("==== EVT ======", time_set[k])
                evt(time_set[k], read_json_file("config_file.json"))

        # Ghi dữ liệu của "_" vào file myVal.txt
        # with open("result.txt", "w") as saveV:
        #     json.dump(data, saveV)
    return render_template("formSchedule.html")


if __name__ == '__main__':
    app.run(debug=True)
    SECRET_KEY = os.urandom(32)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.secret_key = SECRET_KEY
