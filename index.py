import json
import os
from json import JSONDecodeError
import requests

from flask import Flask, render_template, request, flash, redirect, url_for, session

from lib import writeFile, readFileScheduleData, writeFileScheduleData, executeFile

app = Flask(__name__)


@app.route('/schedule', methods=['GET', 'POST'])
def form_schedule():
    global data, config_file_dict, time_set, service_name_request, config_file_requests, \
        time_set_request, time_save
    if request.method == 'POST':
        try:
            # Lấy cookies từ request
            # cookies = request.cookies
            service_name_request = request.form.get('service_name')
            config_file_requests = request.form.get('config_file')
            time_set_request = request.form.get('time_set_hidden')

            # Lưu thông tin vào cookie\
            session["service_name"] = service_name_request
            session["config_file"] = config_file_requests
            session["time_set_hidden"] = time_set_request

            # print("=====time_set_request ==== ", time_set_request)
            # print(f" config_file_requests ==================== {config_file_requests}")
            # print(f"file_name ========= {service_name_request} ")

            if time_set_request:  # Kiểm tra xem time_set_request có rỗng không
                time_set = json.loads(time_set_request)

            # lưu dữ liệu form schedule thành file.json

            file_name = service_name_request + ".json"
            path = os.path.join("botData", file_name)  # tạo đường dẫn chuẩn
            # print("path ======== ", path)

            old = readFileScheduleData()
            # tạo dict để lưu vào scheduleData loại bỏ thành phần không có giá trị (ví dụ: "EVT" = []) và lưu vào
            # dict schedulaData time_set : [service_name]
            for key in time_set.keys():
                if time_set[key]:
                    for ts in time_set[key]:
                        if key == "EVM":
                            d = ts["day"]
                            if len(d) == 1:
                                d = "0" + d
                            h = ts["hour"]
                            time_save = d + "_" + h
                            print("sau định dạng của EVM ============ ", time_save)
                        # duyệt mảng giá trị của key và check với scheduleData, nếu key = EVM thì thay đổi định dạng
                        # và lưu dưới dạng dHHmmss
                        else:
                            time_save = ts

                        if time_save not in old:
                            # print(f"add {time_save} vào old thôiiiiiiiii")
                            old[time_save] = [path]
                        else:
                            # print("old[time_save] =========== ", old[time_save])
                            old[time_save].append(path)
                        writeFileScheduleData(old)
            # nếu file không đúng format json sẽ báo lỗi JSONDecodeError
            config_file_dicts = json.loads(config_file_requests)
            # print("TYPE của list config_file_requests ==============", type(config_file_requests))
            # check service_name exists trước khi lưu
            if not os.path.exists(path):
                data = {
                    "service_name": service_name_request,
                    "config_file": config_file_dicts,
                    "time_set": time_set
                }
                # Ghi dữ liệu JSON vào tệp
                writeFile(path, data)
            else:
                session["service_name"] = service_name_request
                session["config_file"] = config_file_requests
                session["time_set_hidden"] = time_set_request

                print("cookie service_name =============== ", session.get("service_name"))
                print(f"cookie config_file ==================== ", session.get("config_file"))

                flash("Tên dịch vụ đã tồn tại. Vui lòng nhập lại!", 'error')
                # return redirect('/schedule')
                return render_template("formSchedule.html",
                                       service_name=session.get("service_name"),
                                       config_file=session.get("config_file"),
                                       time_set_hidden=session.get("time_set_hidden"))
        except JSONDecodeError as e:
            flash("Nội dung config chưa chính xác, vui lòng kiểm tra lại!!!", 'error')
            # return redirect('/schedule')
            return render_template("formSchedule.html",
                                   service_name=session.get("service_name"),
                                   config_file=session.get("config_file"),
                                   time_set_hidden=session.get("time_set_hidden"))
    return render_template("formSchedule.html")  # , messages=request.args.get("messages")


if __name__ == '__main__':
    SECRET_KEY = os.urandom(32)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.secret_key = SECRET_KEY
    app.run(debug=True)
