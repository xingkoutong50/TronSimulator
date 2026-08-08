import csv
import os
from collections import defaultdict


folder = "game_data"


games = [
    "6s",
    "9s",
    "15s",
    "30s",
    "1min"
]


WINDOW = 5



def load(file):

    data = []

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row.get("单双") in ["单","双"]:

                data.append(row)

    return data





def predict(train):

    patterns = defaultdict(
        lambda:{
            "单":0,
            "双":0
        }
    )


    # 建立历史模式

    for i in range(
        len(train)-WINDOW
    ):

        key = tuple(
            x["尾数"]
            for x in train[i:i+WINDOW]
        )


        result = train[i+WINDOW]["单双"]


        patterns[key][result] += 1



    current_key = tuple(
        x["尾数"]
        for x in train[-WINDOW:]
    )



    if current_key not in patterns:

        return None



    single = patterns[current_key]["单"]

    double = patterns[current_key]["双"]


    total = single + double


    if total < 5:

        return None



    if single > double:

        return "单"

    else:

        return "双"







def backtest(file):


    data = load(file)


    hit=0
    miss=0
    skip=0


    max_wrong=0
    wrong=0



    for i in range(
        WINDOW,
        len(data)
    ):


        train = data[:i]


        prediction = predict(
            train
        )


        if prediction is None:

            skip += 1

            continue



        real = data[i]["单双"]



        if prediction == real:

            hit += 1

            wrong = 0


        else:

            miss += 1

            wrong += 1

            if wrong > max_wrong:

                max_wrong = wrong



    total = hit + miss


    print("--------------------")

    print(
        "数据:",
        file
    )


    print(
        "测试:",
        total
    )


    print(
        "跳过:",
        skip
    )


    print(
        "命中:",
        hit
    )


    print(
        "错误:",
        miss
    )


    if total:

        print(
            "命中率:",
            round(
                hit/total*100,
                2
            ),
            "%"
        )


    print(
        "最大连错:",
        max_wrong
    )






print("====================")
print("Hash走势序列回测")
print("====================")



for game in games:


    path=f"{folder}/{game}.csv"


    if os.path.exists(path):

        backtest(path)