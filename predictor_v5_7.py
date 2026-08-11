import csv
from collections import defaultdict


folder = "game_data"


games = [
    "15s",
    "30s"
]



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



        single=stats[key]["单"]

        double=stats[key]["双"]


        sample=single+double



        if sample < 5:

            continue



        single_p=single/sample*100


        # 防止极端概率

        if single_p>65:

            single_p=65


        if single_p<35:

            single_p=35



        double_p=100-single_p



        return (

            round(single_p,2),

            round(double_p,2),

            f"Hash {length}位",

            sample

        )



    return 50,50,"无有效Hash",0






def confidence(sample):


    if sample>=30:

        return "高"


    elif sample>=10:

        return "中"


    else:

        return "低"






def run(game):


    data=load(
        f"{folder}/{game}.csv"
    )


    single,double,model,sample = hash_predict(data)



    if single > double:

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
        "样本:",
        sample
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

    print(
        "预测:",
        result
    )






print("====================")
print("TRON重点预测 V5.7")
print("====================")


for game in games:

    run(game)


print("====================")