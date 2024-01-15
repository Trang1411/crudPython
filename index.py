import json
import os
from json import JSONDecodeError

from flask import Flask, render_template, request, flash, session, redirect
from werkzeug.utils import secure_filename

from lib import writeFile, readFileScheduleData, writeFileScheduleData, deleteInScheduleData
import zipfile

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
        # Lấy file zip config + ảnh (nếu có)
        # config_file_requests = request.files["file"]
        # service_name = config_file_requests.filename
        # config_file_requests.save(service_name + ".zip")

        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Giải nén file
        with zipfile.ZipFile(file.filename, "r") as zip_file:
            zip_file.extractall("botData")

        # # Giải nén file zip
        # with config_file_requests.ZipFile(service_name + ".zip", "r") as zip_ref:
        #     zip_ref.extractall("botData")  # giải nén và lưu sang botData

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
        print(f"key search ========= {key_search}")
        if ".json" not in key_search:
            key_search = key_search + ".json"
        path = os.path.join("botData", key_search)  # tạo đường dẫn chuẩn
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
    path = os.path.join("botData", service_name)  # tạo đường dẫn chuẩn
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

        file_name = service_name_request + ".json"
        path = os.path.join("botData", file_name)  # tạo đường dẫn chuẩn

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

        deleteInScheduleData(file_name)
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
                    # và lưu dưới dạng dd_hhmmss
                    else:
                        time_save = ts
                    if time_save not in old:
                        print(f"chưa có {time_save} ---------------")
                        # print(f"add {time_save} vào old thôiiiiiiiii")
                        old[time_save] = [file_name]
                    else:
                        print(f"dịch vụ {service_name_request} chưa có trong {time_save} ----------------")
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
        return redirect('/getAllService')
    else:
        svn = request.args["service_name"]
        data = get_service(svn)
        # print(f" data ::::::::::::::::::::: {data}")
        service_name_get = data.get("service_name")
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
