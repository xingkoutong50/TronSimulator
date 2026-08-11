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


def load_data(file):

    data = []

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)


        for row in reader:

            # 强制读取单双字段
            value = row.get("单双")


            if value in ["单", "双"]:

                data.append(value)


    return data



def longest_streak(data, target):

    max_count = 0
    current = 0


    for x in data:

        if x == target:

            current += 1


            if current > max_count:

                max_count = current

        else:

            current = 0


    return max_count




def analyze(file):


    data = load_data(file)


    total = len(data)


    single = data.count("单")

    double = data.count("双")



    print("--------------------")

    print(
        "玩法:",
        file
    )


    print(
        "总期数:",
        total
    )


    if total > 0:

        print(
            "单:",
            single,
            "比例:",
            round(single / total * 100,2),
            "%"
        )


        print(
            "双:",
            double,
            "比例:",
            round(double / total * 100,2),
            "%"
        )


    print(
        "最长连单:",
        longest_streak(
            data,
            "单"
        )
    )


    print(
        "最长连双:",
        longest_streak(
            data,
            "双"
        )
    )


    print(
        "最近20期:",
        "".join(
            data[-20:]
        )
    )





print("====================")

print("新版五玩法分析")

print("====================")



for game in games:


    path = f"{folder}/{game}.csv"


    if os.path.exists(path):

        analyze(path)



print("====================")

print("五玩法分析完成")

print("====================")