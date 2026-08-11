import csv
import os


folder = "game_data"


games = [
    "6s",
    "9s",
    "15s",
    "30s",
    "1min"
]


def analyze(file):

    data = []

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:
            data.append(row["单双"])



    # 记录：
    # 连续N次后，下一次结果

    single_after = {}
    double_after = {}


    for i in range(len(data)-1):

        current = data[i]

        count = 1


        # 往前统计连续长度
        j = i - 1

        while j >= 0 and data[j] == current:

            count += 1
            j -= 1



        next_result = data[i+1]


        if current == "单":

            if count not in single_after:
                single_after[count] = {
                    "单":0,
                    "双":0
                }

            single_after[count][next_result] += 1



        else:

            if count not in double_after:
                double_after[count] = {
                    "单":0,
                    "双":0
                }

            double_after[count][next_result] += 1



    print("====================")
    print(file)
    print("====================")


    print("【连续单之后】")


    for n in sorted(single_after):

        if n <= 10:

            total = (
                single_after[n]["单"]
                +
                single_after[n]["双"]
            )

            if total > 3:

                print(
                    "单连续",
                    n,
                    "次后:",
                    "下一单",
                    single_after[n]["单"],
                    "下一双",
                    single_after[n]["双"],
                    "单概率",
                    round(
                        single_after[n]["单"]/total*100,
                        2
                    ),
                    "%"
                )


    print()


    print("【连续双之后】")


    for n in sorted(double_after):

        if n <= 10:

            total = (
                double_after[n]["单"]
                +
                double_after[n]["双"]
            )

            if total > 3:

                print(
                    "双连续",
                    n,
                    "次后:",
                    "下一单",
                    double_after[n]["单"],
                    "下一双",
                    double_after[n]["双"],
                    "双概率",
                    round(
                        double_after[n]["双"]/total*100,
                        2
                    ),
                    "%"
                )



for game in games:

    path = f"{folder}/{game}.csv"

    if os.path.exists(path):

        analyze(path)