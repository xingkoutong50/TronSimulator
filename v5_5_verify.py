import csv
import os


log_file = "prediction_log.csv"


if not os.path.exists(log_file):

    print("没有找到 prediction_log.csv")

    exit()



rows=[]


with open(
    log_file,
    "r",
    encoding="utf-8"
) as f:

    reader=csv.DictReader(f)

    for row in reader:

        rows.append(row)



print("====================")
print("V5.5开奖验证")
print("====================")


for row in rows:

    print("--------------------")

    print(
        "时间:",
        row["时间"]
    )

    print(
        "玩法:",
        row["玩法"]
    )

    print(
        "模型:",
        row["模型"]
    )

    print(
        "预测:",
        row["预测"]
    )


    result=input(
        "输入实际开奖结果(单/双，跳过输入回车): "
    )


    if result in ["单","双"]:

        row["实际结果"]=result


        if result==row["预测"]:

            row["命中"]="是"

        else:

            row["命中"]="否"


    else:

        row["实际结果"]=""

        row["命中"]=""





with open(
    log_file,
    "w",
    newline="",
    encoding="utf-8"
) as f:


    fieldnames=[

        "时间",
        "玩法",
        "模型",
        "预测",
        "单概率",
        "双概率",
        "实际结果",
        "命中"

    ]


    writer=csv.DictWriter(
        f,
        fieldnames=fieldnames
    )


    writer.writeheader()

    writer.writerows(rows)



print("====================")
print("验证完成")
print("====================")