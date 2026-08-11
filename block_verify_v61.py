import csv
import os
import time
from datetime import datetime


games = [
    "15s",
    "30s"
]


log_file = "block_prediction_log.csv"



def load_csv(game):

    file = f"game_data/{game}.csv"

    data=[]

    with open(
        file,
        "r",
        encoding="gbk",
        errors="ignore"
    ) as f:

        reader=csv.reader(f)

        rows=list(reader)


    for row in rows[1:]:

        if len(row)<6:
            continue


        # 第2列 区块
        block=row[1]

        # 第5列 尾数
        tail=row[4]

        # 第6列 单双
        result=row[5]


        if result.startswith("鍗"):

            result="单"

        elif result.startswith("鍙"):

            result="双"

        else:

            continue


        data.append({

            "block":block,

            "result":result,

            "tail":tail

        })


    return data





def predict(game):


    data=load_csv(game)


    latest=data[-1]


    # 这里先采用简单预测
    # 后面接入V6 Hash模型


    single=0
    double=0


    for x in data[-20:]:

        if x["result"]=="单":

            single+=1

        else:

            double+=1



    if single>double:

        pred="单"

    else:

        pred="双"



    return {

        "block":latest["block"],

        "predict":pred

    }





def save_log(row):


    exists=os.path.exists(log_file)


    with open(
        log_file,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:


        writer=csv.DictWriter(
            f,
            fieldnames=[
                "时间",
                "玩法",
                "预测区块",
                "预测",
                "开奖区块",
                "实际",
                "结果"
            ]
        )


        if not exists:

            writer.writeheader()


        writer.writerow(row)








def wait_new_block(game,old_block):


    print(
        "等待新区块:",
        game
    )


    while True:


        data=load_csv(game)


        latest=data[-1]


        if latest["block"] != old_block:

            return latest


        time.sleep(3)









print("====================")
print("V6.1自动区块验证")
print("====================")



for game in games:


    p=predict(game)


    print("--------------------")

    print(
        "玩法:",
        game
    )

    print(
        "预测区块:",
        p["block"]
    )


    print(
        "预测:",
        p["predict"]
    )



    new=wait_new_block(
        game,
        p["block"]
    )



    if new["result"]==p["predict"]:

        result="命中"

    else:

        result="错误"



    print(
        "开奖区块:",
        new["block"]
    )

    print(
        "实际:",
        new["result"]
    )

    print(
        "结果:",
        result
    )



    save_log({

        "时间":
        datetime.now()
        .strftime("%Y-%m-%d %H:%M:%S"),

        "玩法":
        game,

        "预测区块":
        p["block"],

        "预测":
        p["predict"],

        "开奖区块":
        new["block"],

        "实际":
        new["result"],

        "结果":
        result

    })



print("====================")
print("验证完成")
print("====================")