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




# 根据历史尾数学习
def build_model(history):


    stats={}


    for row in history:


        n=row["尾数"]


        result=row["单双"]



        if n not in stats:

            stats[n]={
                "单":0,
                "双":0
            }



        stats[n][result]+=1



    return stats





def predict(history,current):


    stats=build_model(history)


    n=current["尾数"]


    if n not in stats:

        return None



    single=stats[n]["单"]

    double=stats[n]["双"]



    if single+double < 10:

        return None



    if single > double:

        return "单"

    else:

        return "双"







def test(file):


    data=load(file)


    hit=0

    miss=0

    skip=0


    max_miss=0

    current_miss=0



    for i in range(50,len(data)):


        history=data[:i]


        current=data[i]



        result=predict(
            history,
            current
        )


        if result is None:

            skip+=1

            continue



        real=current["单双"]



        if result==real:

            hit+=1

            current_miss=0


        else:

            miss+=1

            current_miss+=1


            if current_miss>max_miss:

                max_miss=current_miss



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
            round(hit/total*100,2),
            "%"
        )


    print(
        "最大连错:",
        max_miss
    )







print("====================")

print("Hash尾数历史回测")

print("====================")



for game in games:


    path=f"{folder}/{game}.csv"


    if os.path.exists(path):

        test(path)