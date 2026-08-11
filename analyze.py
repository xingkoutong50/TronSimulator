import csv


file_name = "history.csv"


single = 0
double = 0

big = 0
small = 0

max_single = 0
max_double = 0

current_single = 0
current_double = 0


total = 0


with open(
    file_name,
    "r",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)


    for row in reader:

        total += 1


        # 单双统计
        if row["单双"] == "单":

            single += 1
            current_single += 1
            current_double = 0

        else:

            double += 1
            current_double += 1
            current_single = 0


        # 最大连单
        if current_single > max_single:
            max_single = current_single


        # 最大连双
        if current_double > max_double:
            max_double = current_double



        # 大小统计
        if row["大小"] == "大":
            big += 1
        else:
            small += 1



print("====================")
print("TRON历史数据分析")
print("====================")


print("总数据:", total)

print()

print("单双统计:")
print("单:", single)
print("双:", double)

print()

print("大小统计:")
print("大:", big)
print("小:", small)

print()

print("最长连单:", max_single)
print("最长连双:", max_double)