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


# ======================
# 数据读取
# ======================

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



# ======================
# Hash V2模型
# ======================

def hash_v2_predict(data):

    stats=defaultdict(
        lambda:{
            "单":0,
            "双":0
        }
    )


    for i in range(len(data)-3):

        key=(
            data[i]["尾数"],
            data[i+1]["尾数"],
            data[i+2]["尾数"]
        )


        result=data[i+3]["单双"]

        stats[key][result]+=1



    key=(
        data[-3]["尾数"],
        data[-2]["尾数"],
        data[-1]["尾数"]
    )


    if key not in stats:

        return None



    if stats[key]["单"] > stats[key]["双"]:

        return "单"

    else:

        return "双"





# ======================
# V4模型
# ======================

def v4_predict(data):


    single=0
    double=0


    # 最近20期

    recent=data[-20:]


    s=sum(
        1 for x in recent
        if x["单双"]=="单"
    )


    d=len(recent)-s


    single+=s

    double+=d



    # 连续状态

    last=data[-1]["单双"]

    count=1


    for i in range(len(data)-2,-1,-1):

        if data[i]["单双"]==last:

            count+=1

        else:

            break



    if last=="单":

        if count>=3:

            double+=3

        else:

            single+=2


    else:

        if count>=3:

            single+=3

        else:

            double+=2



    if single>double:

        return "单"

    else:

        return "双"





# ======================
# 回测
# ======================

def test_model(data, model):

    hit=0
    total=0


    for i in range(50,len(data)):

        history=data[:i]


        pred=model(history)


        if pred is None:

            continue


        total+=1


        if pred==data[i]["单双"]:

            hit+=1



    if total==0:

        return 0


    return round(
        hit/total*100,
        2
    )





print("====================")
print("模型自动比较")
print("====================")


for game in games:


    path=f"{folder}/{game}.csv"


    if not os.path.exists(path):

        continue



    data=load(path)


    hash_rate=test_model(
        data,
        hash_v2_predict
    )


    v4_rate=test_model(
        data,
        v4_predict
    )


    print("--------------------")

    print(game)


    print(
        "Hash V2:",
        hash_rate,
        "%"
    )


    print(
        "V4:",
        v4_rate,
        "%"
    )



    if hash_rate>v4_rate:

        print(
            "采用: Hash V2"
        )

    else:

        print(
            "采用: V4"
        )



print("====================")