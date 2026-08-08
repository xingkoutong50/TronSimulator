import csv
import os


INPUT = "history.csv"

OUT = "game_data"


games = {
    "6s":2,
    "9s":3,
    "15s":5,
    "30s":10,
    "1min":20
}



os.makedirs(
    OUT,
    exist_ok=True
)



data=[]


with open(
    INPUT,
    "r",
    encoding="utf-8"
) as f:


    reader=csv.DictReader(f)


    for row in reader:

        data.append(row)



for name,step in games.items():


    file=f"{OUT}/{name}.csv"


    with open(
        file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:


        writer=csv.writer(f)


        writer.writerow([
            "时间",
            "区块高度",
            "Hash",
            "Hash尾6",
            "尾数",
            "单双",
            "大小"
        ])


        count=0


        for row in data:


            height=int(row["区块高度"])


            if height % step == 0:


                writer.writerow([
    row["时间"],
    row["区块高度"],
    row["Hash"],
    row.get("Hash尾6", row["Hash"][-6:]),
    row["尾数"],
    row["单双"],
    row["大小"]
])


                count+=1



        print(
            name,
            "期数:",
            count
        )


print("====================")
print("新版五玩法拆分完成")
print("====================")