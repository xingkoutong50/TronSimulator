import csv
import os
import time
from datetime import datetime


games = [
    "15s",
    "30s"
]


log_file = "block_prediction_log.csv"



def load_game(game):

    file = f"game_data/{game}.csv"

    data=[]


    if not os.path.exists(file):
        return data


    with open(
        file,
        "r",
        encoding="gbk",
        errors="ignore"
    ) as f:


        reader=csv.reader(f)

        rows=list(reader)



    for row in rows[1:]:


        if len(row)<7:
            continue


        block=row[1].strip()


        tail=row[5].strip()


        result=row[6].strip()


        if result.startswith("鍗"):

            result="单"


        elif result.startswith("鍙"):

            result="双"


        else:

            continue



        data.append({

            "block":block,

            "tail":tail,

            "result":result

        })


    return data





def simple_predict(data):


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







def watch(game):


    data=load_game(game)


    if len(data)<20:

        print(game,"数据不足")

        return



    latest=data[-1]


    predict=simple_predict(data)



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
        predict
    )


    print(
        "等待下一开奖..."
    )



    old_block=latest["block"]



    while True:


        time.sleep(3)


        new_data=load_game(game)


        if len(new_data)==0:

            continue



        new=new_data[-1]



        if new["block"] != old_block:


            if new["result"]==predict:

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
                old_block,

                "预测":
                predict,

                "开奖区块":
                new["block"],

                "实际":
                new["result"],

                "结果":
                result

            })


            break







print("====================")
print("V6.2自动区块验证")
print("====================")



for game in games:

    watch(game)



print("====================")
print("验证结束")
print("====================")