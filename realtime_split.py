import csv
import os
import time


source = "history.csv"

out_dir = "game_data"


os.makedirs(out_dir, exist_ok=True)



def split():

    if not os.path.exists(source):
        return


    with open(
        source,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:

        rows = list(csv.reader(f))


    if len(rows) <= 1:
        return


    header = rows[0]

    data = rows[1:]


    # 五种玩法区块间隔
    games = {

        "6s":6,

        "9s":9,

        "15s":15,

        "30s":30,

        "1min":60

    }


    total=len(data)



    for name,interval in games.items():


        step=max(1,int(interval/6))


        result=data[::step]


        with open(
            f"{out_dir}/{name}.csv",
            "w",
            newline="",
            encoding="utf-8"
        ) as f:


            writer=csv.writer(f)

            writer.writerow(header)

            writer.writerows(result)



    print(
        "同步完成:",
        total,
        "条"
    )





print("====================")
print("实时数据同步启动")
print("====================")


while True:

    try:

        split()

    except Exception as e:

        print(e)


    time.sleep(5)