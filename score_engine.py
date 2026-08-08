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


def load_data(file):

    data = []

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:
            data.append(row["单双"])

    return data



def score(data):

    single_score = 0
    double_score = 0


    total = len(data)


    if total == 0:
        return 0,0,"无数据"



    # 规则1 历史比例

    single = data.count("单")
    double = data.count("双")


    if single > double:
        single_score += 1
    else:
        double_score += 1



    # 规则2 最近20期

    recent = data[-20:]

    r_single = recent.count("单")
    r_double = recent.count("双")


    if r_single > r_double:
        double_score += 1
    else:
        single_score += 1



    # 规则3 当前连挂

    last = data[-1]

    streak = 0


    for x in reversed(data):

        if x == last:
            streak += 1
        else:
            break



    if streak >= 5:

        if last == "单":
            double_score += 1
        else:
            single_score += 1



    # 规则4 最近冷热

    recent50 = data[-50:]

    if recent50.count("单") < recent50.count("双"):

        single_score += 1

    else:

        double_score += 1



    # 规则5 总判断

    if single_score > double_score:

        result = "单"

    elif double_score > single_score:

        result = "双"

    else:

        result = "平"



    return (
        single_score,
        double_score,
        result
    )





print("====================")
print("五玩法评分预测")
print("====================")


results = []


for game in games:


    file = f"{folder}/{game}.csv"


    if os.path.exists(file):

        data = load_data(file)


        s,d,r = score(data)


        print("--------------------")

        print(
            game,
            "期数:",
            len(data)
        )

        print(
            "单分:",
            s,
            "双分:",
            d
        )

        print(
            "预测:",
            r
        )


        results.append(r)



print("====================")

print("综合投票")


print(
    "单票:",
    results.count("单")
)

print(
    "双票:",
    results.count("双")
)


if results.count("单") > results.count("双"):

    print("最终预测: 单")

elif results.count("双") > results.count("单"):

    print("最终预测: 双")

else:

    print("最终预测: 平")