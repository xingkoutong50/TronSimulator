import csv
import time
import os
from datetime import datetime
from collections import defaultdict


games = [
    "15s",
    "30s"
]


log_file = "block_prediction_log_v65.csv"



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

        reader = csv.reader(f)

        rows = list(reader)



    for row in rows[1:]:

        if len(row) < 6:
            continue


        block = row[1]

        try:
            tail = int(row[4])
        except:
            continue


        result = "单" if tail % 2 else "双"


        data.append({

            "block": block,
            "tail": str(tail),
            "result": result

        })


    return data






# Hash模式回测

def hash_model(data):


    best = None



    for length in [3,2,1]:


        table = defaultdict(
            lambda:{
                "单":0,
                "双":0,
                "total":0,
                "hit":0
            }
        )



        for i in range(
            len(data)-length-1
        ):


            key = "".join(
                x["tail"]
                for x in data[i:i+length]
            )


            real = data[i+length]["result"]


            table[key][real]+=1

            table[key]["total"]+=1



        key = "".join(
            x["tail"]
            for x in data[-length:]
        )



        if key not in table:
            continue



        single = table[key]["单"]

        double = table[key]["双"]

        total = single + double



        if total < 5:
            continue



        predict = (
            "单"
            if single > double
            else "双"
        )


        rate = max(single,double)/total*100



        if best is None or rate > best["rate"]:


            best = {

                "model":
                f"Hash {length}位",

                "sample":
                total,

                "rate":
                round(rate,2),

                "predict":
                predict

            }



    if best:

        return best



    return {

        "model":"无",

        "sample":0,

        "rate":50,

        "predict":"双"

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
                "time",
                "game",
                "model",
                "predict_block",
                "predict",
                "open_block",
                "tail",
                "actual",
                "result"
            ]
        )


        if not exists:

            writer.writeheader()


        writer.writerow(row)







def verify(game):


    data=load_game(game)


    if len(data)<50:

        print(game,"数据不足")

        return



    latest=data[-1]


    model=hash_model(data)



    print("--------------------")

    print(
        "玩法:",
        game
    )


    print(
        "模型:",
        model["model"]
    )


    print(
        "历史表现:",
        model["rate"],
        "%"
    )


    print(
        "样本:",
        model["sample"]
    )


    print(
        "预测区块:",
        latest["block"]
    )


    print(
        "预测:",
        model["predict"]
    )


    print(
        "等待开奖..."
    )



    old_block=latest["block"]



    while True:


        time.sleep(3)


        new_data=load_game(game)


        new=new_data[-1]



        if new["block"] != old_block:


            actual=new["result"]


            if actual == model["predict"]:

                result="命中"

            else:

                result="错误"



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
                actual
            )


            print(
                "结果:",
                result
            )



            save_log({

                "time":
                datetime.now()
                .strftime("%Y-%m-%d %H:%M:%S"),

                "game":game,

                "model":
                model["model"],

                "predict_block":
                old_block,

                "predict":
                model["predict"],

                "open_block":
                new["block"],

                "tail":
                new["tail"],

                "actual":
                actual,

                "result":
                result

            })


            break







print("====================")
print("V6.5 Hash智能验证")
print("====================")


for game in games:

    verify(game)



print("====================")
print("结束")
print("====================")