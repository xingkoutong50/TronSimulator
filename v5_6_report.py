import csv
import os
from collections import defaultdict


log_file = "prediction_log.csv"



if not os.path.exists(log_file):

    print("没有找到 prediction_log.csv")

    exit()



total = 0
verified = 0
hit = 0


game_stat = defaultdict(
    lambda:{
        "total":0,
        "verified":0,
        "hit":0
    }
)


model_stat = defaultdict(
    lambda:{
        "total":0,
        "verified":0,
        "hit":0
    }
)



with open(
    log_file,
    "r",
    encoding="utf-8"
) as f:


    reader = csv.DictReader(f)


    for row in reader:


        total += 1


        game = row["玩法"]

        model = row["模型"]


        game_stat[game]["total"] += 1

        model_stat[model]["total"] += 1



        result = row.get("实际结果","")


        if result in ["单","双"]:


            verified += 1

            game_stat[game]["verified"] += 1

            model_stat[model]["verified"] += 1



            if row["命中"] == "是":

                hit += 1

                game_stat[game]["hit"] += 1

                model_stat[model]["hit"] += 1






print("====================")
print("V5.6真实运行报告")
print("====================")


print()

print(
    "总预测:",
    total
)

print(
    "已验证:",
    verified
)


if verified:

    print(
        "整体命中率:",
        round(
            hit/verified*100,
            2
        ),
        "%"
    )

else:

    print(
        "整体命中率: 暂无数据"
    )



print("--------------------")

print("玩法表现")


for game,data in game_stat.items():


    if data["verified"]:


        rate = round(
            data["hit"]/
            data["verified"]*
            100,
            2
        )


    else:

        rate = 0



    print(
        game,
        "预测:",
        data["total"],
        "验证:",
        data["verified"],
        "命中率:",
        rate,
        "%"
    )



print("--------------------")

print("模型表现")


for model,data in model_stat.items():


    if data["verified"]:


        rate = round(
            data["hit"]/
            data["verified"]*
            100,
            2
        )

    else:

        rate = 0



    print(
        model,
        "预测:",
        data["total"],
        "验证:",
        data["verified"],
        "命中率:",
        rate,
        "%"
    )



print("====================")