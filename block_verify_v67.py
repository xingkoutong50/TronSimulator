import csv
import time
import os
from datetime import datetime
from collections import defaultdict


games = [
    "6s",
    "9s",
    "15s",
    "30s",
    "1min"
]


log_file = "block_prediction_log_v67.csv"



def load_game(game):

    # ========== 改成读取 history_{game}.csv ==========
    file = f"history_{game}.csv"

    data=[]

    if not os.path.exists(file):
        return data


    with open(
        file,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:

        rows=list(csv.reader(f))


    for row in rows[1:]:

        if len(row)<7:
            continue

        try:
            block=row[1]
            tail=int(row[4])
        except:
            continue


        result="单" if tail%2 else "双"


        data.append({

            "block":block,
            "tail":str(tail),
            "result":result

        })


    return data





def choose_model(data):


    best=None


    for length in [3,2,1]:


        table=defaultdict(
            lambda:{
                "单":0,
                "双":0
            }
        )


        for i in range(len(data)-length):

            key="".join(
                x["tail"]
                for x in data[i:i+length]
            )


            real=data[i+length]["result"]

            table[key][real]+=1



        key="".join(
            x["tail"]
            for x in data[-length:]
        )


        if key not in table:
            continue



        s=table[key]["单"]
        d=table[key]["双"]

        total=s+d


        if total<5:
            continue



        predict="单" if s>d else "双"

        rate=max(s,d)/total*100


        score=rate*(total/(total+10))


        item={

            "model":f"Hash {length}位",

            "predict":predict,

            "rate":round(rate,2),

            "score":round(score,2)

        }


        if best is None or score>best["score"]:

            best=item



    if best:
        return best


    return {

        "model":"默认",

        "predict":"双",

        "rate":50,

        "score":0

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






def run_game(game):


    data=load_game(game)


    if len(data)<50:

        print(game,"数据不足")

        return



    now=data[-1]


    model=choose_model(data)


    print("--------------------")
    print("玩法:",game)
    print("模型:",model["model"])
    print("历史:",model["rate"],"%")
    print("预测区块:",now["block"])
    print("预测:",model["predict"])
    print("等待开奖...")


    old=now["block"]


    while True:

        time.sleep(3)

        new_data=load_game(game)

        if not new_data:
            continue

        new=new_data[-1]


        if new["block"]!=old:


            actual=new["result"]


            result=(
                "命中"
                if actual==model["predict"]
                else "错误"
            )


            print("开奖区块:",new["block"])
            print("尾数:",new["tail"])
            print("实际:",actual)
            print("结果:",result)


            save_log({

                "time":
                datetime.now()
                .strftime("%Y-%m-%d %H:%M:%S"),

                "game":game,

                "model":model["model"],

                "predict_block":old,

                "predict":model["predict"],

                "open_block":new["block"],

                "tail":new["tail"],

                "actual":actual,

                "result":result

            })


            break







print("====================")
print("V6.7自动运行模式")
print("====================")


while True:


    for game in games:

        run_game(game)


    print("等待下一轮...")


    time.sleep(2)