import requests


API_KEY = "d8ed34a4-61be-4b24-aa9c-292b6b67be9b"

url = "https://api.trongrid.io/wallet/getnowblock"

headers = {
    "TRON-PRO-API-KEY": API_KEY
}


r = requests.post(
    url,
    headers=headers,
    timeout=10
)

data = r.json()


height = data["block_header"]["raw_data"]["number"]

block_hash = data["blockID"]


# 去掉字母，只保留数字

numbers = ""

for c in block_hash:
    if c.isdigit():
        numbers += c


last = int(numbers[-1])


print("=====================")
print("TRON开奖采集测试")
print("=====================")

print("区块:", height)

print("Hash:")
print(block_hash)

print("尾数:", last)


if last % 2 == 1:
    print("单双: 单")
else:
    print("单双: 双")


if last >= 5:
    print("大小: 大")
else:
    print("大小: 小")