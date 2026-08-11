import csv
import time
import os


games = [
    "15s",
    "30s"
]


def load_game(game):

    file = f"game_data/{game}.csv"

    data=[]

    if not os.path.exists(file):
        return data


    with open(
        file,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:

        reader=csv.reader(f)

        rows=list(reader)


    for row in rows[1:]:

        if len(row)<6:
            continue


        block=row[1]

        tail=row[4]


        try:
            num=int(tail)

        except:
            continue


        if num % 2 == 1:
            result="单"
        else:
            result="双"


        data.append({

            "block":block,

            "tail":num,

            "result":result

        })


    return data





def predict(data):


    single=0
    double=0


    for x in data[-20:]:

        if x["result"]=="单":
            single+=1
        else:
            double+=1



    if single>double:
        return "单"

    else:
        return "双"






def watch(game):


    data=load_game(game)


    if len(data)<20:

        print(game,"数据不足")

        return



    latest=data[-1]


    pred=predict(data)



    print("--------------------")

    print(
        "玩法:",
        game
    )

    print(
        "当前区块:",
        latest["block"]
    )

    print(
        "预测:",
        pred
    )

    print(
        "等待开奖..."
    )


    old=latest["block"]



    while True:


        time.sleep(3)


        data=load_game(game)


        if len(data)==0:
            continue



        new=data[-1]


        if new["block"] != old:


            print(
                "开奖区块:",
                new["block"]
            )

            print(
                "尾数:",
                new["tail"]
            )

            print(
                "实际:",
                new["result"]
            )


            if new["result"]==pred:

                print("结果: 命中")

            else:

                print("结果: 错误")


            break






print("====================")
print("V6.3自动区块验证")
print("====================")


for game in games:

    watch(game)


print("====================")
print("结束")
print("====================")