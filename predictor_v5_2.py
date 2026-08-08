import csv
import os
from collections import defaultdict


folder = "game_data"


games = [
    "6s",
    "9s",
    "15s",
    "30s",
    "1min"
]


# 最新回测结果
model_rate = {

    "6s": {
        "model":"V4",
        "rate":50.58
    },

    "9s": {
        "model":"Hash V2",
        "rate":47.37
    },

    "15s": {
        "model":"Hash V2",
        "rate":58.68
    },

    "30s": {
        "model":"Hash V2",
        "rate":57.69
    },

    "1min": {
        "model":"Hash V2",
        "rate":42.86
    }

}



best_model = {

    "6s":"V4",
    "9s":"Hash",
    "15s":"Hash",
    "30s":"Hash",
    "1min":"Hash"

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


        for i in range(
            len(data)-length
        ):


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



        if sample < 5:

            continue



        single=s/sample*100

        double=d/sample*100



        # 防止极端值

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



    last=data[-1]["单双"]

    count=1


    for i in range(
        len(data)-2,
        -1,
        -1
    ):

        if data[i]["单双"]==last:

            count+=1

        else:

            break



    if last=="单" and count>=3:

        d+=3


    elif last=="双" and count>=3:

        s+=3



    total=s+d


    return (

        round(s/total*100,2),

        round(d/total*100,2),

        "V4",

        20

    )







def confidence(sample):


    if sample>=30:

        return "高"


    elif sample>=10:

        return "中"


    else:

        return "低"








def run(game):


    file=f"{folder}/{game}.csv"


    data=load(file)



    if best_model[game]=="Hash":


        single,double,model,sample=hash_predict(data)



        if sample==0:

            single,double,model,sample=v4(data)



    else:


        single,double,model,sample=v4(data)





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
        "当前样本:",
        sample
    )



    print(
        "历史表现:",
        model_rate[game]["rate"],
        "%"
    )



    print(
        "单概率:",
        single,
        "%"
    )


    print(
        "双概率:",
        double,
        "%"
    )



    print(
        "置信:",
        confidence(sample)
    )



    if single>double:

        print(
            "预测: 单"
        )

    else:

        print(
            "预测: 双"
        )







print("====================")
print("TRON智能预测 V5.2")
print("====================")



for game in games:

    if os.path.exists(
        f"{folder}/{game}.csv"
    ):

        run(game)



print("====================")