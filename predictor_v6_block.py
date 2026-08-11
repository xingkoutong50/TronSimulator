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
        encoding="gbk",
        errors="ignore"
    ) as f:

        reader=csv.reader(f)

        rows=list(reader)


    for row in rows[1:]:

        if len(row)<6:
            continue


        tail=row[4].strip()

        result=row[5].strip()


        # 乱码单双转换

        if result.startswith("鍗"):
            result="单"

        elif result.startswith("鍙"):
            result="双"

        else:
            continue



        data.append({

            "单双":result,

            "尾数":tail,

            "区块":row[1],

            "Hash":row[2]

        })


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



        if sample<5:

            continue



        sp=s/sample*100

        if sp>65:
            sp=65

        if sp<35:
            sp=35


        dp=100-sp


        return {

            "模型":f"Hash {length}位",

            "样本":sample,

            "单":round(sp,2),

            "双":round(dp,2),

            "预测":
                "单" if sp>dp else "双"

        }



    return {

        "模型":"无",

        "样本":0,

        "单":50,

        "双":50,

        "预测":"双"

    }







def run(game):


    data=load(
        f"{folder}/{game}.csv"
    )


    if len(data)==0:

        print(game,"没有有效数据")

        return



    latest=data[-1]


    result=hash_predict(data)



    print("--------------------")

    print("玩法:",game)

    print(
        "最新开奖区块:",
        latest["区块"]
    )

    print(
        "模型:",
        result["模型"]
    )

    print(
        "参考样本:",
        result["样本"]
    )

    print(
        "单概率:",
        result["单"],
        "%"
    )

    print(
        "双概率:",
        result["双"],
        "%"
    )

    print(
        "下一期预测:",
        result["预测"]
    )



print("====================")
print("TRON区块预测 V6")
print("====================")


for game in games:

    run(game)


print("====================")