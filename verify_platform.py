import csv


file = "history.csv"


print("====================")
print("TRON开奖规则验证")
print("====================")


count = 0


with open(
    file,
    "r",
    encoding="utf-8"
) as f:


    reader = csv.DictReader(f)


    for row in reader:


        count += 1


        height = row["区块高度"]
        hash_value = row["Hash"]
        result = row["单双"]
        number = row["尾数"]


        print("--------------------")

        print(
            "区块:",
            height
        )


        print(
            "Hash:",
            hash_value
        )


        print(
            "取尾数:",
            number
        )


        print(
            "程序结果:",
            result
        )


        print(
            "平台结果: 待输入"
        )


        if count >= 20:
            break



print("====================")
print("验证结束")
print("====================")