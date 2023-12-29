import json
import os

from flask import Flask, render_template, request, jsonify

from lib import (readFileScheduleData, writeFileScheduleData,
                 writeFile)

def schedule():
    # đọc file scheduleData (chứa thông tin service_name và time_set tương ứng)
    with open("scheduleData.json", "r") as f:
        data = json.load(f)

    for k, v in data.items():
        print(k, v)
    # for item in my_schedule:

    # if time_set["EVD"] != []:
    #     # print("==== EVD ======", time_set["EVD"])
    #     evd(time_set["EVD"], read_json_file(file_name))
    # if time_set["EVT"] != []:
    #     print("==== EVT ======", time_set["EVT"])
    #     evt(time_set["EVT"], read_json_file(file_name))
    return

if __name__ == '__main__':
    schedule()