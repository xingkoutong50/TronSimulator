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


# 当前最佳模型
best_model = {

    "6s": "V4",
    "9s": "V4",
    "15s": "Hash V2",
    "30s": "Hash V2",
    "1min": "V4"

}



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





# ======================
# Hash V2
# ======================

def hash_v2(data):


    if len(data) < 20:

        return 50,50,0



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

        return 50,50,0



    single = stats[key]["单"]

    double = stats[key]["双"]


    sample = single + double



    # 小样本保护

    if sample < 5:

        return 50,50,sample



    single_p = single / sample * 100

    double_p = double / sample * 100



    return (

        round(single_p,2),

        round(double_p,2),

        sample

    )







# ======================
# V4
# ======================

def v4(data):


    recent = data[-20:]


    single = sum(
        1 for x in recent
        if x["单双"]=="单"
    )


    double = len(recent)-single



    # 连续状态

    last = data[-1]["单双"]

    count = 1



    for i in range(
        len(data)-2,
        -1,
        -1
    ):

        if data[i]["单双"] == last:

            count += 1

        else:

            break




    if last=="单" and count>=3:

        double += 3


    elif last=="双" and count>=3:

        single += 3




    total = single + double



    return (

        round(single/total*100,2),

        round(double/total*100,2),

        total

    )








def run(game):


    file = f"{folder}/{game}.csv"


    data = load(file)



    model = best_model[game]



    if model=="Hash V2":


        single,double,sample = hash_v2(data)



        # Hash样本不足自动切V4

        if sample < 5:


            model = "V4"

            single,double,sample = v4(data)



    else:


        single,double,sample = v4(data)





    print("--------------------")

    print(
        "玩法:",
        game
    )


    print(
        "模型:",
        model
    )


    print(
        "参考样本:",
        sample
    )


    print(
        "单概率:",
        single,
        "%"
    )


    print(
        "双概率:",
        double,
        "%"
    )



    if single > double:

        print(
            "预测: 单"
        )

    else:

        print(
            "预测: 双"
        )







print("====================")

print("TRON智能预测 V5")

print("====================")



for game in games:


    if os.path.exists(
        f"{folder}/{game}.csv"
    ):

        run(game)



print("====================")