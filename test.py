import json

with open("myVal.txt", "rb") as rf:
    data = json.load(rf)
print(data)
