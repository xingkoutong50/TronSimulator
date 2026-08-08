import csv
import os
from collections import defaultdict


log_file = "prediction_log.csv"



if not os.path.exists(log_file):

    print("没有找到预测日志")

    exit()



total = 0


games = defaultdict(int)

models = defaultdict(int)

results = defaultdict(int)



with open(
    log_file,
    "r",
    encoding="utf-8"
) as f:


    reader = csv.DictReader(f)


    for row in reader:


        total += 1


        games[row["玩法"]] += 1


        models[row["模型"]] += 1


        results[row["预测"]] += 1






print("====================")

print("V5.4预测日志分析")

print("====================")


print()

print(
    "总预测次数:",
    total
)



print("--------------------")

print("玩法统计")


for k,v in games.items():

    print(
        k,
        ":",
        v
    )



print("--------------------")

print("模型使用")


for k,v in models.items():

    print(
        k,
        ":",
        v
    )



print("--------------------")

print("单双预测")


for k,v in results.items():

    print(
        k,
        ":",
        v
    )


print("====================")