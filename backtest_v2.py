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


    # 规则1 历史比例

    if data.count("单") > data.count("双"):
        single += 1
    else:
        double += 1



    # 规则2 最近20

    recent = data[-20:]

    if recent.count("单") > recent.count("双"):
        single += 1
    else:
        double += 1



    # 规则3 连挂学习

    last = data[-1]

    count = 1

    for x in reversed(data[:-1]):

        if x == last:
            count += 1
        else:
            break



    same = 0
    other = 0


    for i in range(len(data)-1):

        if data[i] != last:
            continue


        c = 1

        j = i-1

        while j >= 0 and data[j] == last:
            c += 1
            j -= 1


        if c == count:

            if data[i+1] == last:
                same += 1
            else:
                other += 1



    if same + other >= 10:

        if same > other:

            if last == "单":
                single += 1
            else:
                double += 1

        else:

            if last == "单":
                double += 1
            else:
                single += 1



    # 规则4 最近50

    recent50 = data[-50:]


    if recent50.count("单") > recent50.count("双"):

        single += 1

    else:

        double += 1



    if single > double:
        return "单"

    else:
        return "双"





def test(file):

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


        result = predict(history)


        real = data[i]


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

    print("数据:", file)

    print("测试:", total)

    print("命中:", hit)

    print("错误:", miss)

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
print("V2历史回测")
print("====================")


for game in games:

    path = f"{folder}/{game}.csv"

    if os.path.exists(path):

        test(path)