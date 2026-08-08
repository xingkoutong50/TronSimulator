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


LOOKBACK = 5



def load(file):

    data = []

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:
            data.append(row["单双"])

    return data



# 计算相似度
def similarity(a, b):

    same = 0

    for x,y in zip(a,b):

        if x == y:
            same += 1

    return same



def predict(data):

    current = data[-LOOKBACK:]


    result = []



    # 搜索历史

    for i in range(
        LOOKBACK,
        len(data)-1
    ):


        old = data[i-LOOKBACK:i]


        score = similarity(
            current,
            old
        )


        # 至少4个相同才记录

        if score >= 4:


            result.append(
                {
                    "score":score,
                    "next":data[i]
                }
            )



    if len(result)==0:

        return None



    single = 0
    double = 0


    # 高相似优先

    for r in result:


        weight = r["score"]


        if r["next"]=="单":

            single += weight

        else:

            double += weight



    if single > double:

        final="单"

    else:

        final="双"



    return {

        "matches":len(result),

        "single_score":single,

        "double_score":double,

        "predict":final

    }




print("====================")
print("V3.1模糊走势匹配")
print("====================")



for game in games:


    path=f"{folder}/{game}.csv"


    if os.path.exists(path):


        data=load(path)


        print("--------------------")

        print(game)


        r=predict(data)


        if r:

            print(r)

        else:

            print("无相似走势")
