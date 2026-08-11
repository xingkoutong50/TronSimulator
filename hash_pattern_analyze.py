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

    data = []


    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)


        for row in reader:

            # 只保留正确单双
            if row.get("单双") in ["单","双"]:

                data.append(row)


    return data




def analyze(data):


    stats = {}


    for i in range(len(data)-1):


        now = data[i]


        number = now["尾数"]


        next_result = data[i+1]["单双"]


        if number not in stats:

            stats[number] = {
                "单":0,
                "双":0
            }



        stats[number][next_result] += 1



    return stats





print("====================")
print("Hash尾数模式分析")
print("====================")



for game in games:


    path=f"{folder}/{game}.csv"


    if os.path.exists(path):


        print("--------------------")

        print(game)


        data=load(path)


        stats=analyze(data)



        for n in sorted(stats):


            total = (
                stats[n]["单"]
                +
                stats[n]["双"]
            )


            if total >= 10:


                print(
                    "尾数",
                    n,
                    "样本:",
                    total,
                    "单:",
                    stats[n]["单"],
                    "双:",
                    stats[n]["双"],
                    "单比例:",
                    round(
                        stats[n]["单"]/total*100,
                        2
                    ),
                    "%"
                )



print("====================")
print("分析完成")
print("====================")