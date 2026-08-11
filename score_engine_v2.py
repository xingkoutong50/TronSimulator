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



# 连挂学习
def streak_score(data):

    last = data[-1]

    count = 1


    for x in reversed(data[:-1]):

        if x == last:
            count += 1
        else:
            break


    same = 0
    other = 0


    # 找历史相同连挂情况

    for i in range(len(data)-1):

        if data[i] != last:
            continue


        c = 1

        j = i-1

        while j >= 0 and data[j] == last:

            c += 1
            j -= 1


        if c == count:

            if data[i+1] == last:
                same += 1
            else:
                other += 1



    total = same + other


    if total < 10:

        return 0,0,count,total


    if same > other:

        if last == "单":
            return 1,0,count,total
        else:
            return 0,1,count,total


    else:

        if last == "单":
            return 0,1,count,total
        else:
            return 1,0,count,total




def predict(data):

    single = 0
    double = 0



    # 规则1 历史比例

    if data.count("单") > data.count("双"):

        single += 1

    else:

        double += 1



    # 规则2 最近20

    recent = data[-20:]

    if recent.count("单") > recent.count("双"):

        single += 1

    else:

        double += 1



    # 规则3 连挂学习

    s,d,count,total = streak_score(data)


    single += s
    double += d



    # 规则4 最近50冷热

    recent50 = data[-50:]


    if recent50.count("单") > recent50.count("双"):

        single += 1

    else:

        double += 1



    if single > double:

        result = "单"

    elif double > single:

        result = "双"

    else:

        result = "平"



    return (
        single,
        double,
        result,
        count,
        total
    )





print("====================")
print("V2评分预测")
print("====================")


results = []


for game in games:


    file = f"{folder}/{game}.csv"


    if os.path.exists(file):

        data = load_data(file)


        s,d,r,c,t = predict(data)


        print("--------------------")

        print(
            game,
            "数据:",
            len(data)
        )

        print(
            "当前连:",
            c
        )

        print(
            "历史样本:",
            t
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
print("综合结果")


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