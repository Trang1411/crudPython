import json
import os
from json import JSONDecodeError

from flask import Flask, render_template, request, flash, session, redirect

from lib import writeFile, readFileScheduleData, writeFileScheduleData

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@app.route('/schedule', methods=['GET', 'POST'])
def form_schedule():
    global data, time_set, service_name_request, config_file_requests, \
        time_save
    if request.method == 'POST':

        # Lấy thông tin từ request
        token_telegram_request = request.form.get("token_telegram")
        group_id_request = request.form.get("group_id")
        service_name_request = request.form.get('service_name')
        config_file_requests = request.form.get('config_file')
        evd = request.form.getlist('evd[]')
        evt = request.form.getlist('evt[]')
        evm = request.form.getlist('evm[]')

        # Lưu thông tin vào cookie
        session["service_name"] = service_name_request
        session["token_telegram"] = token_telegram_request
        session["group_id"] = group_id_request
        session["config_file"] = config_file_requests
        session["evd"] = evd
        session["evt"] = evt
        session["evm"] = evm

        time_set = {}
        if evt:
            time_set["EVT"] = evt
        if evm:
            time_set["EVM"] = evm
        if evd:
            time_set["EVD"] = evd
        # print("time set ============ ", time_set)
        # print("TYPE time set ===== ", type(time_set))

        file_name = service_name_request + ".json"
        path = os.path.join("botData", file_name)  # tạo đường dẫn chuẩn
        # print("path ======== ", path)

        try:
            # nếu  không đúng format json sẽ báo lỗi JSONDecodeError
            config_file_dicts = json.loads(config_file_requests)  # chuyển str config thành đối tượng python
            print("TYPE config dict :::::::: ", type(config_file_dicts))
            #  nếu config rỗng s báo lỗi
            if len(config_file_dicts) == 0:
                flash("Bạn chưa nhập nội dung config, vui lòng kiểm tra lại!!!", 'error')
                return render_template("formSchedule.html",
                                       service_name=session.get("service_name"),
                                       token_telegram=session.get("token_telegram"),
                                       group_id=session.get("group_id"),
                                       config_file=session.get("config_file"),
                                       evt=session.get("evt"), evd=session.get("evd"), evm=session.get("evm"))
        except JSONDecodeError as e:
            print("eeeeeeeeeeeeeeeeeeeeeeeee ====== ", e)
            flash("Nội dung config chưa chính xác, vui lòng kiểm tra lại!!!", 'error')
            return render_template("formSchedule.html",
                                   service_name=session.get("service_name"),
                                   token_telegram=session.get("token_telegram"),
                                   group_id=session.get("group_id"),
                                   config_file=session.get("config_file"),
                                   evt=session.get("evt"), evd=session.get("evd"), evm=session.get("evm"))

        # nếu tên dịch vụ (đường dẫn) đã tồn tại -> thông báo lỗi
        if os.path.exists(path):
            session["service_name"] = service_name_request
            session["config_file"] = config_file_requests

            # print("cookie service_name =============== ", session.get("service_name"))
            # print(f"cookie config_file ==================== ", session.get("config_file"))

            flash("Tên dịch vụ đã tồn tại. Vui lòng nhập lại!", 'error')
            # return redirect('/schedule')
            return render_template("formSchedule.html",
                                   service_name=session.get("service_name"),
                                   token_telegram=session.get("token_telegram"),
                                   group_id=session.get("group_id"),
                                   config_file=session.get("config_file"),
                                   evt=session.get("evt"), evd=session.get("evd"), evm=session.get("evm"))
        #  Ngược lại, tên dịch vụ chưa tồn tại -> thêm
        else:
            if not os.path.exists(path):
                old = readFileScheduleData()
                # tạo dict để lưu vào scheduleData loại bỏ thành phần không có giá trị (ví dụ: "EVT" = []) và lưu vào
                for key in time_set.keys():
                    if time_set[key]:
                        for ts in time_set[key]:
                            if key == "EVM":
                                # print("TYPE value of evm ", type(ts))
                                d = ts[:2]
                                h = ts[3:]
                                time_save = d + "_" + h
                                print("sau định dạng của EVM ============ ", time_save)
                            # duyệt mảng giá trị của key và check với scheduleData, nếu key = EVM thì thay đổi định dạng
                            # và lưu dưới dạng d_hhmmss
                            else:
                                time_save = ts
                            if time_save not in old:
                                # print(f"add {time_save} vào old thôiiiiiiiii")
                                old[time_save] = [file_name]
                            else:
                                if path not in old[time_save]:
                                    old[time_save].append(file_name)
                            writeFileScheduleData(old)
                data = {
                    "service_name": service_name_request,
                    "token_telegram": token_telegram_request,
                    "group_id": group_id_request,
                    "config_file": config_file_dicts,
                    "time_set": time_set
                }
                # Ghi dữ liệu JSON vào tệp
                writeFile(path, data)
    return render_template("formSchedule.html")  # , messages=request.args.get("messages")


@app.route('/getAllService', methods=['GET'])
def get_all_service():
    global files
    if request.method == 'GET':
        path = "botData"
        files = os.listdir(path)
        # print(f"TYPE của files ===== {type(files)}")
        # print(f"Các file trong fiels là : {files}")
    return render_template("getAllService.html", files=files)


@app.route('/searchService', methods=['GET', 'POST'])
def search_service():
    global key_search
    result_search = None
    if request.method == "POST":
        key_search = request.form.get("service_name")
        key_search = key_search + ".json"
        path = os.path.join("botData", key_search)  # tạo đường dẫn chuẩn
        if os.path.exists(path):
            with open(path, "r") as rf:
                result_search_dict = json.load(rf)
            # print(f"this is data search ========= {result_search_dict}")
            result_search = json.dumps(result_search_dict)
            return result_search
    return result_search


@app.route('/updateService', methods=['GET', 'POST'])
def update_service():
    global data, time_set, service_name_request, config_file_requests, \
        time_save
    if request.method == 'POST':

        # Lấy thông tin từ request
        token_telegram_request = request.form.get("token_telegram")
        group_id_request = request.form.get("group_id")
        service_name_request = request.form.get('service_name')
        config_file_requests = request.form.get('config_file')
        evd = request.form.getlist('evd[]')
        evt = request.form.getlist('evt[]')
        evm = request.form.getlist('evm[]')

        # Lưu thông tin vào cookie
        session["service_name"] = service_name_request
        session["token_telegram"] = token_telegram_request
        session["group_id"] = group_id_request
        session["config_file"] = config_file_requests
        session["evd"] = evd
        session["evt"] = evt
        session["evm"] = evm

        time_set = {}
        if evt:
            time_set["EVT"] = evt
        if evm:
            time_set["EVM"] = evm
        if evd:
            time_set["EVD"] = evd
        # print("time set ============ ", time_set)
        # print("TYPE time set ===== ", type(time_set))

        file_name = service_name_request + ".json"
        path = os.path.join("botData", file_name)  # tạo đường dẫn chuẩn
        # print("path ======== ", path)

        try:
            # nếu  không đúng format json sẽ báo lỗi JSONDecodeError
            config_file_dicts = json.loads(config_file_requests)  # chuyển str config thành đối tượng python
            print("TYPE config dict :::::::: ", type(config_file_dicts))
            #  nếu config rỗng s báo lỗi
            if len(config_file_dicts) == 0:
                flash("Bạn chưa nhập nội dung config, vui lòng kiểm tra lại!!!", 'error')
                return render_template("formSchedule.html",
                                       service_name=session.get("service_name"),
                                       token_telegram=session.get("token_telegram"),
                                       group_id=session.get("group_id"),
                                       config_file=session.get("config_file"),
                                       evt=session.get("evt"), evd=session.get("evd"), evm=session.get("evm"))
        except JSONDecodeError as e:
            print("eeeeeeeeeeeeeeeeeeeeeeeee ====== ", e)
            flash("Nội dung config chưa chính xác, vui lòng kiểm tra lại!!!", 'error')
            return render_template("formSchedule.html",
                                   service_name=session.get("service_name"),
                                   token_telegram=session.get("token_telegram"),
                                   group_id=session.get("group_id"),
                                   config_file=session.get("config_file"),
                                   evt=session.get("evt"), evd=session.get("evd"), evm=session.get("evm"))

        # nếu tên dịch vụ (đường dẫn) không tồn tại -> thông báo lỗi
        if not os.path.exists(path):
            session["service_name"] = service_name_request
            session["config_file"] = config_file_requests

            # print("cookie service_name =============== ", session.get("service_name"))
            # print(f"cookie config_file ==================== ", session.get("config_file"))

            flash("Tên dịch vụ Không tồn tại. Vui lòng nhập lại!", 'error')
            return render_template("formSchedule.html",
                                   service_name=session.get("service_name"),
                                   token_telegram=session.get("token_telegram"),
                                   group_id=session.get("group_id"),
                                   config_file=session.get("config_file"),
                                   evt=session.get("evt"), evd=session.get("evd"), evm=session.get("evm"))
        #  Ngược lại, tên dịch vụ có tồn tại -> thêm
        else:
            if os.path.exists(path):
                old = readFileScheduleData()
                os.remove(path)  # xóa file cũ để ghi file mới (sau khi cập nhật thông tin)
                # tạo dict để lưu vào scheduleData loại bỏ thành phần không có giá trị (ví dụ: "EVT" = []) và lưu vào
                for key in time_set.keys():
                    if time_set[key]:
                        for ts in time_set[key]:
                            if key == "EVM":
                                # print("TYPE value of evm ", type(ts))
                                d = ts[:2]
                                h = ts[3:]
                                time_save = d + "_" + h
                                print("sau định dạng của EVM ============ ", time_save)
                            # duyệt mảng giá trị của key và check với scheduleData, nếu key = EVM thì thay đổi định dạng
                            # và lưu dưới dạng dd_hhmmss
                            else:
                                time_save = ts
                            if time_save not in old:
                                # print(f"add {time_save} vào old thôiiiiiiiii")
                                old[time_save] = [file_name]
                            else:
                                if path not in old[time_save]:
                                    old[time_save].append(file_name)
                            writeFileScheduleData(old)
                data = {
                    "service_name": service_name_request,
                    "token_telegram": token_telegram_request,
                    "group_id": group_id_request,
                    "config_file": config_file_dicts,
                    "time_set": time_set
                }
                # Ghi dữ liệu JSON vào tệp
                writeFile(path, data)
    return render_template("formUpdate.html")


@app.route('/deleteService', methods=['GET', 'POST'])
def delete_service():
    if request.method == 'POST':
        file_del = request.form.get("service_name")
        print(f" ================ want delete file {file_del}")
        path = os.path.join("botData", file_del)  # tạo đường dẫn chuẩn
        os.remove(path)
    return render_template("getAllService.html")


if __name__ == '__main__':
    SECRET_KEY = os.urandom(32)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.secret_key = SECRET_KEY
    app.run(debug=True)
