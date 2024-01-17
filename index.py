import json
import os
import shutil
from json import JSONDecodeError

from flask import Flask, render_template, request, flash, session, redirect
from werkzeug.utils import secure_filename

from lib import writeFile, checkhhmmss
import zipfile

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@app.route('/schedule', methods=['GET', 'POST'])
def form_schedule():
    global data, evm, evd, evt
    if request.method == 'POST':

        # Lấy file zip config + ảnh (nếu có)
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join('temp', filename))
        service_name = file.filename.replace(".zip", "")

        # Giải nén file
        with zipfile.ZipFile(os.path.join("temp", file.filename), "r") as zip_file:
            zip_file.extractall("temp")

        # Xóa file
        os.remove(os.path.join("temp", file.filename))
        path = os.path.join("temp", service_name, "config.json")  # tạo đường dẫn chuẩn
        # print("path ======== ", path)

        try:
            # đọc file config.json
            with open(path, 'r') as file:
                data = json.load(file)

            print(data.get("time_set"))

            token_telegram_val = data.get("token_telegram")
            group_id_val = data.get("group_id")
            config_file_val = data.get("config_file")  # cần check nội dung
            time_set_val = data.get("time_set")
            # check valid time_set
            if "EVT" in time_set_val:
                evt = time_set_val["EVT"]
                if not evt:
                    flash("Thời gian không hợp lệ, vui lòng kiểm tra lại!!!", 'error')
                    return render_template("formSchedule.html")
                for time_evt in evt:
                    if time_evt <= 0:
                        flash("Khoảng thời gian giữa 2 lần thực thi không hợp lệ, vui lòng kiểm tra lại!!!", 'error')
                        return render_template("formSchedule.html")
            if "EVD" in time_set_val:
                evd = time_set_val["EVD"]
                if not evd:
                    flash("Thời gian không hợp lệ, vui lòng kiểm tra lại!!!", 'error')
                    return render_template("formSchedule.html")
                for time_evd in evd:
                    if checkhhmmss(time_evd) is False:
                        flash("Thời gian thực thi hàng ngày không hợp lệ, vui lòng kiểm tra lại!!!", 'error')
                        return render_template("formSchedule.html")
            if "EVM" in time_set_val:
                evm = time_set_val["EVM"]
                if not evm:
                    flash("Thời gian không hợp lệ, vui lòng kiểm tra lại!!!", 'error')
                    return render_template("formSchedule.html")
                for time_evm in time_set_val["EVM"]:
                    if len(time_evm) != 11:
                        flash("Thời gian thực thi hàng tháng không hợp lệ, vui lòng kiểm tra lại !!!", 'error')
                        return render_template("formSchedule.html")
                    else:
                        parts = time_evm.split(' ')
                        day = int(parts[0])
                        hour = parts[1]
                        if checkhhmmss(hour) is False or 0 <= day > 31:
                            flash("Thời gian thực thi hàng tháng không hợp lệ, vui lòng kiểm tra lại !!!", 'error')
                            return render_template("formSchedule.html")

            #  nếu config rỗng -> báo lỗi
            if len(data) == 0 or config_file_val == []:
                flash("Bạn chưa nhập nội dung config, vui lòng kiểm tra lại!!!", 'error')
                return render_template("formSchedule.html")

            # check format của file config có đủ key-value không
            if len(data) != 4 or (token_telegram_val or group_id_val or config_file_val or time_set_val) is None:
                flash("Bạn chưa nhập đủ nội dung config, vui lòng kiểm tra lại!!!", 'error')
                return render_template("formSchedule.html")
        except JSONDecodeError as e:
            print("eeeeeeeeeeeeeeeeeeeeeeeee ====== ", e)
            flash("Nội dung config chưa chính xác, vui lòng kiểm tra lại!!!", 'error')
            return render_template("formSchedule.html")

        # nếu tên dịch vụ (đường dẫn) đã tồn tại -> thông báo lỗi
        path_botData = os.path.join("botData")
        if service_name in os.listdir(path_botData):
            flash("Tên dịch vụ đã tồn tại. Vui lòng nhập lại!", 'error')
            return render_template("formSchedule.html")
        #  Ngược lại, tên dịch vụ chưa tồn tại -> lưu folder vào botData
        else:
            # di chuyển folder vào botData (nơi lưu cuối)
            path_folder = os.path.join("temp", service_name)
            print(f"=========== di chuyển từ {path_folder} sang {path_botData}")
            # Di chuyển file
            shutil.move(path_folder, path_botData)
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
        print(f"key search ========= {key_search}")
        path = os.path.join("botData", key_search, "config.json")  # tạo đường dẫn chuẩn
        if os.path.exists(path):
            with open(path, "r") as rf:
                result_search_dict = json.load(rf)
            # print(f"this is data search ========= {result_search_dict}")
            result_search = json.dumps(result_search_dict)
            return result_search
    return result_search


def get_service(service_name):
    global evt, evd, evm, token_telegram, group_id, config_file, time_set_data
    print("=================================================================================")
    print(f"service name update ========= {service_name}")
    path = os.path.join("botData", service_name, "config.json")  # tạo đường dẫn chuẩn
    if os.path.exists(path):
        with open(path, "r") as rf:
            result_search_dict = json.load(rf)
        return result_search_dict


@app.route('/updateService', methods=['GET', 'POST'])
def update_service():
    global data, time_set, service_name_request, config_file_requests, config, str, \
        time_save, token_telegram_get, service_name_get, group_id_get, config_file_get, time_set_get, evt_get, evd_get, evm_get
    if request.method == 'POST':
        # Lấy thông tin từ request
        token_telegram_request = request.form.get("token_telegram")
        group_id_request = request.form.get("group_id")
        service_name_request = request.form.get("service_name")
        config_file_requests = request.form.get("config_file")
        evd = request.form.getlist('evd[]')
        evt = request.form.getlist('evt[]')
        evm = request.form.getlist('evm[]')

        path = os.path.join("botData", service_name_request, "config.json")  # tạo đường dẫn chuẩn

        print(f"service_name_request ::::::: {service_name_request}")
        print(f"group_id_request ::::::: {group_id_request}")

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
        # print("path ======== ", path)

        try:
            # nếu  không đúng format json -> báo lỗi JSONDecodeError
            config_file_dicts = json.loads(config_file_requests)  # chuyển str config thành đối tượng python

            # print("TYPE config dict :::::::: ", type(config_file_dicts))
            #  nếu config rỗng -> báo lỗi
            if len(config_file_dicts) == 0:
                flash("Bạn chưa nhập nội dung config, vui lòng kiểm tra lại!!!", 'error')
                return render_template("formUpdate.html",
                                       service_name=session.get("service_name"),
                                       token_telegram=session.get("token_telegram"),
                                       group_id=session.get("group_id"),
                                       config_file=session.get("config_file"),
                                       evt=session.get("evt"), evd=session.get("evd"), evm=session.get("evm"))
        except JSONDecodeError as e:
            print("eeeeeeeeeeeeeeeeeeeeeeeee ====== ", e)
            flash("Nội dung config chưa chính xác, vui lòng kiểm tra lại!!!", 'error')
            return render_template("formUpdate.html",
                                   service_name=session.get("service_name"),
                                   token_telegram=session.get("token_telegram"),
                                   group_id=session.get("group_id"),
                                   config_file=session.get("config_file"),
                                   evt=session.get("evt"), evd=session.get("evd"), evm=session.get("evm"))

        data = {
            "service_name": service_name_request,
            "token_telegram": token_telegram_request,
            "group_id": group_id_request,
            "config_file": config_file_dicts,
            "time_set": time_set
        }
        # Ghi dữ liệu JSON vào tệp
        writeFile(path, data)
        return redirect('/getAllService')
    else:
        svn = request.args["service_name"]
        data = get_service(svn)
        # print(f" data ::::::::::::::::::::: {data}")
        service_name_get = svn
        token_telegram_get = data.get("token_telegram")
        group_id_get = data.get("group_id")
        config_file_get = data.get("config_file")
        config = json.dumps(config_file_get)
        # print(f"file in config :::: {file}")
        print(f"config :::::::: {config_file_get}")
        time_set_get = data.get("time_set")
        if time_set_get.get("EVT"):
            evt_get = time_set_get["EVT"]
        else:
            evt_get = []
        if time_set_get.get("EVD"):
            evd_get = time_set_get["EVD"]
        else:
            evd_get = []
        if time_set_get.get("EVM"):
            evm_get = time_set_get["EVM"]
        else:
            evm_get = []

        return render_template("formUpdate.html", service_name=service_name_get,
                               token_telegram=token_telegram_get, group_id=group_id_get,
                               config_file=config, time_set_data=time_set_get,
                               evt=evt_get, evd=evd_get, evm=evm_get)


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
