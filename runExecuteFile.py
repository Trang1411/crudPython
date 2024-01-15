import os

import schedule
import time

from lib import readFile, evt, evd, evm

if __name__ == '__main__':
    botDatas = files = os.listdir("botData")
    print(f"botDatas ===== {botDatas}")

    for file_name in botDatas:
        path = os.path.join("botData", file_name)  # tạo đường dẫn chuẩn
        datas = readFile(path)  # đọc file

        times = datas["time_set"]  # lấy ra giá trị các thời gian thực thi trong dịch vụ
        # kiểm tra kiểu thời gian thực thi, nếu có -> duyệt mảng các thời điểm cần thực thi
        # -> tạo schedule cho thời điểm đó
        print(f"thời gian của {file_name} là {times}")

        if "EVD" in times:
            for time_evd in times["EVD"]:
                print(f"thời gian của EVD ===== ")
                evd(time_evd, file_name)
        if "EVT" in times:
            for time_evt in times["EVT"]:
                print(f"thời gian của EVT ===== ")
                evt(time_evt, file_name)
        if "EVM" in times:
            for time_evm in times["EVM"]:
                print(f"thời gian của EVM ===== ")
                evm(time_evm, file_name)
    while True:
        schedule.run_pending()
        time.sleep(1)
