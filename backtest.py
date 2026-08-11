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


def predict(data):

    single = 0
    double = 0


    # 历史比例
    if data.count("单") > data.count("双"):
        single += 1
    else:
        double += 1


    # 最近20期
    recent = data[-20:]

    if recent.count("单") > recent.count("双"):
        double += 1
    else:
        single += 1


    # 连续压力

    last = data[-1]

    streak = 0

    for x in reversed(data):

        if x == last:
            streak += 1
        else:
            break


    if streak >= 5:

        if last == "单":
            double += 1
        else:
            single += 1


    if single > double:
        return "单"

    else:
        return "双"



def run_backtest(file):

    data = []

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:
            data.append(row["单双"])


    hit = 0
    miss = 0

    max_miss = 0
    current_miss = 0


    for i in range(50, len(data)-1):

        history = data[:i]

        real = data[i]


        result = predict(history)


        if result == real:

            hit += 1
            current_miss = 0

        else:

            miss += 1
            current_miss += 1


            if current_miss > max_miss:
                max_miss = current_miss



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
        "命中:",
        hit
    )

    print(
        "错误:",
        miss
    )


    print(
        "命中率:",
        round(hit/total*100,2),
        "%"
    )

    print(
        "最大连错:",
        max_miss
    )




print("====================")
print("历史回测")
print("====================")


for game in games:

    path = f"{folder}/{game}.csv"

    if os.path.exists(path):

        run_backtest(path)