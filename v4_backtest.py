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



# Hash走势评分
def hash_score(data):

    if len(data) < 30:

        return 50,50


    stats = defaultdict(
        lambda:{
            "单":0,
            "双":0
        }
    )


    for i in range(len(data)-3):

        key = (
            data[i]["尾数"],
            data[i+1]["尾数"],
            data[i+2]["尾数"]
        )


        result = data[i+3]["单双"]

        stats[key][result] += 1



    key = (
        data[-3]["尾数"],
        data[-2]["尾数"],
        data[-1]["尾数"]
    )


    if key not in stats:

        return 50,50


    s = stats[key]["单"]
    d = stats[key]["双"]


    if s+d == 0:

        return 50,50


    return (
        s/(s+d)*100,
        d/(s+d)*100
    )



# 最近20期
def recent_score(data):

    recent = data[-20:]


    s = sum(
        1 for x in recent
        if x["单双"]=="单"
    )


    d = len(recent)-s


    return (
        s/20*100,
        d/20*100
    )



# 连续走势
def streak_score(data):

    last = data[-1]["单双"]

    count = 1


    for i in range(len(data)-2,-1,-1):

        if data[i]["单双"] == last:

            count += 1

        else:

            break



    if last=="单":

        if count>=3:

            return 45,55

        else:

            return 52,48


    else:

        if count>=3:

            return 55,45

        else:

            return 48,52



def predict(data):


    h1,h2 = hash_score(data)

    s1,s2 = streak_score(data)

    r1,r2 = recent_score(data)



    single = (
        h1*0.4
        +
        s1*0.25
        +
        r1*0.35
    )


    double = (
        h2*0.4
        +
        s2*0.25
        +
        r2*0.35
    )



    if single > double:

        return "单"

    else:

        return "双"




def backtest(file):


    data = load(file)


    hit=0
    miss=0


    max_wrong=0
    wrong=0



    for i in range(50,len(data)):


        history=data[:i]


        prediction=predict(history)


        real=data[i]["单双"]



        if prediction==real:

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
        max_wrong
    )




print("====================")
print("V4历史回测")
print("====================")


for game in games:


    path=f"{folder}/{game}.csv"


    if os.path.exists(path):

        backtest(path)