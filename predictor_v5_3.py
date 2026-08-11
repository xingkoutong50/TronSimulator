import csv
import os
from datetime import datetime
from collections import defaultdict


folder = "game_data"

log_file = "prediction_log.csv"


games = [
    "6s",
    "9s",
    "15s",
    "30s",
    "1min"
]


best_model = {

    "6s":"V4",
    "9s":"Hash",
    "15s":"Hash",
    "30s":"Hash",
    "1min":"Hash"

}



model_rate = {

    "6s":50.58,
    "9s":47.37,
    "15s":58.68,
    "30s":57.69,
    "1min":42.86

}



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





def hash_predict(data):


    for length in [3,2,1]:

        stats=defaultdict(
            lambda:{
                "单":0,
                "双":0
            }
        )


        for i in range(len(data)-length):

            key=tuple(
                x["尾数"]
                for x in data[i:i+length]
            )

            result=data[i+length]["单双"]

            stats[key][result]+=1



        key=tuple(
            x["尾数"]
            for x in data[-length:]
        )


        if key not in stats:

            continue



        s=stats[key]["单"]

        d=stats[key]["双"]


        sample=s+d


        if sample<5:

            continue



        single=s/sample*100


        if single>65:
            single=65


        if single<35:
            single=35



        double=100-single



        return (
            round(single,2),
            round(double,2),
            f"Hash {length}位",
            sample
        )


    return 50,50,"Hash无样本",0






def v4(data):


    recent=data[-20:]


    s=sum(
        1 for x in recent
        if x["单双"]=="单"
    )


    d=20-s



    if s>d:

        s+=1

    else:

        d+=1



    total=s+d


    return (

        round(s/total*100,2),

        round(d/total*100,2),

        "V4",

        20

    )






def save_log(
    game,
    model,
    predict,
    single,
    double
):


    exists=os.path.exists(log_file)


    with open(
        log_file,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:


        writer=csv.writer(f)


        if not exists:

            writer.writerow(
                [
                    "时间",
                    "玩法",
                    "模型",
                    "预测",
                    "单概率",
                    "双概率"
                ]
            )



        writer.writerow(
            [
                datetime.now()
                .strftime("%Y-%m-%d %H:%M:%S"),

                game,

                model,

                predict,

                single,

                double
            ]
        )







def run(game):


    data=load(
        f"{folder}/{game}.csv"
    )


    if best_model[game]=="Hash":


        single,double,model,sample=hash_predict(data)


        if sample==0:

            single,double,model,sample=v4(data)


    else:


        single,double,model,sample=v4(data)



    if single>double:

        result="单"

    else:

        result="双"



    print("--------------------")

    print(
        "玩法:",
        game
    )

    print(
        "模型:",
        model
    )

    print(
        "历史表现:",
        model_rate[game],
        "%"
    )

    print(
        "样本:",
        sample
    )

    print(
        "单:",
        single,
        "%"
    )

    print(
        "双:",
        double,
        "%"
    )

    print(
        "预测:",
        result
    )



    save_log(
        game,
        model,
        result,
        single,
        double
    )







print("====================")
print("TRON智能预测 V5.3")
print("====================")


for game in games:

    if os.path.exists(
        f"{folder}/{game}.csv"
    ):

        run(game)


print("====================")
print("预测已记录")
print("====================")