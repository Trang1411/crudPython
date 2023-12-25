import json
import os

from flask import Flask, render_template, request, jsonify

from lib import (_get, _put, _post, _upload_file,
                 get_value_by_path, get_path, evd, evt)

app = Flask(__name__)


def read_json_file(json_file):
    global file_path
    globalVal = {}
    # Đọc file json
    print("000000000000000000000000", json_file)
    path = os.path.join("botData", json_file)
    with open(path, "r") as file:
        data_file_json = json.load(file)

    # print("======================> ", type(data_file_json))
    # print("======================>> ", data_file_json)
    # Lấy dữ liệu của "_" trong mỗi json và lưu vào globalVal
    config_file_json = data_file_json["config_file"]
    print("config_file_json ========== ", config_file_json)
    # with open(config_file_json, "r", encoding='utd-8') as cf:
    #     config_file = json.load(cf)

    # print("type config_file ========== ", type(config_file))
    for item in config_file_json:
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
        with open("myVal.txt", "w") as saveV:
            json.dump(globalVal, saveV)
    print("SUCCESS!!!!!!!!!!!!!!!!!!!!!!!!!!!")


@app.route('/schedule', methods=['GET', 'POST'])
def form_schedule():
    global data
    if request.method == 'POST':
        service_name = request.form.get('service_name')
        config_file_request = request.form.get('config_file')
        time_set = request.form.get('time_set_hidden')
        # print("config file  ==============>>>> ", config_file_request)

        try:
            time_set = json.loads(time_set)
            config_file_dict = json.loads(config_file_request)
        except json.JSONDecodeError as e:
            print("Lỗi JSON:", e)
            return  # Dừng xử lý nếu phát hiện lỗi JSON

        data = {
            "service_name": service_name,
            "config_file": config_file_dict,
            "time_set": time_set
        }

        # lưu file config thành file.json
        file_name = service_name + ".json"
        path = os.path.join("botData", file_name)  # tạo đường dẫn chuẩn

        # Kiểm tra xem thư mục đã tồn tại hay chưa
        if not os.path.exists("/pyWithJson/botData/"):
            print("check exists ===== ", os.path.exists("/pyWithJson/botData/"))
            os.makedirs("/pyWithJson/botData/", exist_ok=True)  # tạo thư mục nếu chưa tồn tại

        # Ghi dữ liệu JSON vào tệp
        try:
            with open(path, "w") as f:
                json.dump(data, f)  # Ghi dữ liệu JSON trực tiếp
        except Exception as e:
            print("Lỗi ghi file:", e)

        # Đặt tham số newline thành None
        # with open(path, "w", newline="") as c:
        #     c.write(data_json)

        if time_set["EVD"] != []:
            # print("==== EVD ======", time_set["EVD"])
            evd(time_set["EVD"], read_json_file(file_name))
        if time_set["EVT"] != []:
            print("==== EVT ======", time_set["EVT"])
            evt(time_set["EVT"], read_json_file(file_name))

        # Ghi dữ liệu của "_" vào file myVal.txt
        # with open("result.txt", "w") as saveV:
        #     json.dump(data, saveV)
    return render_template("formSchedule.html")


if __name__ == '__main__':
    app.run(debug=True)
    SECRET_KEY = os.urandom(32)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.secret_key = SECRET_KEY
