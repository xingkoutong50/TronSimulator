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



def similarity(a,b):

    same = 0

    for x,y in zip(a,b):

        if x == y:
            same += 1

    return same




def predict(history):


    current = history[-LOOKBACK:]


    matches=[]


    for i in range(
        LOOKBACK,
        len(history)-1
    ):


        old = history[i-LOOKBACK:i]


        score = similarity(
            current,
            old
        )


        if score >=4:

            matches.append(
                {
                    "score":score,
                    "next":history[i]
                }
            )



    if len(matches)==0:

        return None



    single=0
    double=0



    for m in matches:


        weight=m["score"]


        if m["next"]=="单":

            single+=weight

        else:

            double+=weight



    if single>double:

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



    for i in range(
        50,
        len(data)
    ):


        history=data[:i]


        result=predict(history)


        if result is None:

            skip+=1

            continue



        real=data[i]


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

    print("数据:",file)

    print("测试:",total)

    print("跳过:",skip)

    print("命中:",hit)

    print("错误:",miss)


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
print("V3.1模式回测")
print("====================")



for game in games:

    path=f"{folder}/{game}.csv"


    if os.path.exists(path):

        test(path)