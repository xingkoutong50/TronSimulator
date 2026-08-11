import csv
import os


folder = "game_data"


games = [
    "6s",
    "9s",
    "15s",
    "30s",
    "1min"
]


LOOKBACK = 5



def load(file):

    data=[]

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        reader=csv.DictReader(f)

        for row in reader:
            data.append(row["单双"])

    return data



def predict(data):


    if len(data) < LOOKBACK + 20:
        return None


    current = data[-LOOKBACK:]


    same_single = 0
    same_double = 0

    matches = 0



    # 历史搜索

    for i in range(
        LOOKBACK,
        len(data)-1
    ):


        old = data[i-LOOKBACK:i]


        if old == current:


            matches += 1


            if data[i] == "单":

                same_single += 1

            else:

                same_double += 1



    if matches == 0:

        return {
            "matches":0
        }



    if same_single > same_double:

        result="单"

    else:

        result="双"



    return {

        "matches":matches,
        "single":same_single,
        "double":same_double,
        "result":result

    }





print("====================")
print("V3走势模式匹配")
print("====================")



for game in games:


    path=f"{folder}/{game}.csv"


    if os.path.exists(path):


        data=load(path)


        r=predict(data)


        print("--------------------")

        print(game)


        if r:

            print(r)

        else:

            print("数据不足")