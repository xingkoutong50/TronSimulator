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


def load(file):

    data=[]

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        reader=csv.DictReader(f)

        for row in reader:

            if row.get("单双") in ["单","双"]:

                data.append(row)

    return data





def pattern_score(history, length):


    stats=defaultdict(
        lambda:{
            "单":0,
            "双":0
        }
    )


    # 建历史模式

    for i in range(
        len(history)-length
    ):


        key=tuple(
            x["尾数"]
            for x in history[i:i+length]
        )


        result=history[i+length]["单双"]


        stats[key][result]+=1



    current_key=tuple(
        x["尾数"]
        for x in history[-length:]
    )


    if current_key not in stats:

        return 0,0,0



    single=stats[current_key]["单"]

    double=stats[current_key]["双"]


    return (
        single,
        double,
        single+double
    )






def predict(history):


    total_single=0
    total_double=0



    # 3位走势
    s,d,n = pattern_score(
        history,
        3
    )

    if n:

        total_single += s*5

        total_double += d*5



    # 2位走势
    s,d,n = pattern_score(
        history,
        2
    )

    if n:

        total_single += s*3

        total_double += d*3



    # 1位走势
    s,d,n = pattern_score(
        history,
        1
    )

    if n:

        total_single += s

        total_double += d




    if total_single==0 and total_double==0:

        return None



    if total_single > total_double:

        return "单"

    else:

        return "双"






def backtest(file):


    data=load(file)


    hit=0
    miss=0
    skip=0


    max_wrong=0
    wrong=0



    for i in range(
        20,
        len(data)
    ):


        history=data[:i]


        result=predict(
            history
        )


        if result is None:

            skip+=1

            continue



        real=data[i]["单双"]



        if result==real:

            hit+=1

            wrong=0


        else:

            miss+=1

            wrong+=1


            if wrong>max_wrong:

                max_wrong=wrong



    total=hit+miss



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
print("Hash走势V2回测")
print("====================")


for game in games:


    path=f"{folder}/{game}.csv"


    if os.path.exists(path):

        backtest(path)