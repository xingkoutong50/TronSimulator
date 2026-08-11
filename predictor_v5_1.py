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


# 根据最新回测结果选择模型
best_model = {

    "6s": "V4",

    "9s": "Hash",

    "15s": "Hash",

    "30s": "Hash",

    "1min": "Hash"

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





# =========================
# Hash走势模型
# 3位 -> 2位 -> 1位
# =========================

def hash_predict(data):


    for length in [3,2,1]:


        stats = defaultdict(
            lambda:{
                "单":0,
                "双":0
            }
        )


        for i in range(
            len(data)-length
        ):


            key = tuple(
                x["尾数"]
                for x in data[i:i+length]
            )


            result = data[i+length]["单双"]


            stats[key][result] += 1




        key = tuple(
            x["尾数"]
            for x in data[-length:]
        )


        if key not in stats:

            continue



        single = stats[key]["单"]

        double = stats[key]["双"]


        sample = single + double



        # 小样本不用

        if sample < 5:

            continue



        single_p = single / sample * 100

        double_p = double / sample * 100



        # 防止极端概率

        if single_p > 65:

            single_p = 65


        if single_p < 35:

            single_p = 35



        double_p = 100 - single_p



        return (

            round(single_p,2),

            round(double_p,2),

            f"Hash {length}位",

            sample

        )



    return (

        50,

        50,

        "Hash无有效样本",

        0

    )







# =========================
# V4模型
# =========================

def v4(data):


    recent = data[-20:]


    single = sum(

        1 for x in recent

        if x["单双"]=="单"

    )


    double = len(recent)-single



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

        "V4",

        20

    )







def run(game):


    file = f"{folder}/{game}.csv"


    data = load(file)


    if len(data)<30:

        return



    model = best_model[game]



    if model=="Hash":


        single,double,real_model,sample = hash_predict(data)



        if sample==0:


            single,double,real_model,sample = v4(data)



    else:


        single,double,real_model,sample = v4(data)





    print("--------------------")

    print(
        "玩法:",
        game
    )


    print(
        "模型:",
        real_model
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

print("TRON智能预测 V5.1")

print("====================")



for game in games:


    if os.path.exists(
        f"{folder}/{game}.csv"
    ):

        run(game)



print("====================")