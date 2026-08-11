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


# 玩法权重
weights = {
    "6s": 0.15,
    "9s": 0.30,
    "15s": 0.40,
    "30s": 0.10,
    "1min": 0.05
}



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




# Hash走势评分
def hash_score(data):

    if len(data)<20:

        return 50,50


    history=data[:-1]


    stats=defaultdict(
        lambda:{
            "单":0,
            "双":0
        }
    )


    # 三位走势

    for i in range(len(history)-3):

        key=(
            history[i]["尾数"],
            history[i+1]["尾数"],
            history[i+2]["尾数"]
        )


        result=history[i+3]["单双"]


        stats[key][result]+=1



    key=(
        history[-3]["尾数"],
        history[-2]["尾数"],
        history[-1]["尾数"]
    )


    if key not in stats:

        return 50,50


    s=stats[key]["单"]

    d=stats[key]["双"]


    total=s+d


    if total==0:

        return 50,50


    return (
        s/total*100,
        d/total*100
    )





# 连续走势
def streak_score(data):

    last=data[-1]["单双"]

    count=1


    for i in range(
        len(data)-2,
        -1,
        -1
    ):

        if data[i]["单双"]==last:

            count+=1

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






# 最近比例
def recent_score(data):

    recent=data[-20:]


    s=sum(
        1 for x in recent
        if x["单双"]=="单"
    )


    d=len(recent)-s


    return (
        s/20*100,
        d/20*100
    )







def analyze(game):


    path=f"{folder}/{game}.csv"


    data=load(path)


    h1,h2=hash_score(data)

    s1,s2=streak_score(data)

    r1,r2=recent_score(data)



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



    total=single+double


    single=single/total*100

    double=double/total*100

    # 限制概率范围，防止过度自信

    if single > 65:
     single = 65

     if single < 35:
      single = 35


     double = 100 - single



    print("--------------------")

    print(
        game
    )

    print(
        "单概率:",
        round(single,2),
        "%"
    )

    print(
        "双概率:",
        round(double,2),
        "%"
    )


    if single>double:

        print(
            "预测: 单"
        )

    else:

        print(
            "预测: 双"
        )





print("====================")

print("V4概率评分")

print("====================")


for game in games:


    if os.path.exists(
        f"{folder}/{game}.csv"
    ):

        analyze(game)


print("====================")