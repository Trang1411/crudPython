import json
import os
from json import JSONDecodeError

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for

from lib import (evd, evt, evm, writeFile,
                 readFileScheduleData, writeFileScheduleData, executeFile
                 )

app = Flask(__name__)


@app.route('/schedule', methods=['GET', 'POST'])
def form_schedule():
    global data, config_file_dict, time_set, jsonErr, service_name_exists
    if request.method == 'POST':
        service_name_request = request.form.get('service_name')
        config_file_request = request.form.get('config_file')
        time_set_request = request.form.get('time_set_hidden')
        print("time set ==== ", time_set_request)

        try:
            time_set = json.loads(time_set_request)
            config_file_dict = json.loads(config_file_request)  # nếu file rỗng sẽ báo lỗi JSONDecodeError
            # lưu dữ liệu form schedule thành file.json
            file_name = service_name_request + ".json"
            path = os.path.join("botData", file_name)  # tạo đường dẫn chuẩn

            # check service_name exists trước khi lưu
            # service_name_check = checkServiceNameExists(service_name)
            # if service_name_check == True:
            #     flash("Tên dịch vụ đã tồn tại. Vui lòng nhập lại!")
            #     return
            # else:
            data = {
                "service_name": service_name_request,
                "config_file": config_file_dict,
                "time_set": time_set
            }
            # Ghi dữ liệu JSON vào tệp
            try:
                writeFile(path, data)
            except Exception as e:
                print("Lỗi ghi file:", e)

            time_set_add = {}
            # tạo dict để lưu vào scheduleData
            # loại bỏ thành phần không có giá trị (ví dụ: "EVT" = [])
            for key in time_set.keys():
                print("--key----time_set.get(key)----------", key, " ::: ", time_set.get(key))
                if time_set.get(key):
                    time_set_add[key] = time_set.get(key)

            # print("time_set sau khi xóa những phần tử rỗng ::: ", time_set_add)
            schedule_init = {
                "service_name": path,
                "time_set": time_set_add
            }

            old = readFileScheduleData()
            old.append(schedule_init)
            writeFileScheduleData(old)
        except JSONDecodeError as e:
            print(e)
            jsonErr = "Nội dung file config chưa chính xác, vui lòng kiểm tra lại!!!"
            service_name_exists = "Tên dịch vụ đã tồn tại, vui lòng nhập tên khác!!!"

            return redirect(url_for("form_schedule", jsonErr=jsonErr, service_name_exists=service_name_exists))

    # for k, v in request.args.items():
    #     print(f"k = {k}, v = {v}")

    return render_template("formSchedule.html", messages=request.args.get("messages"))


if __name__ == '__main__':

    SECRET_KEY = os.urandom(32)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.secret_key = SECRET_KEY
    app.run(debug=True)
    check = True
    while check:
        executeFile()
