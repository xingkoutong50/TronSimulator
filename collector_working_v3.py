import requests
import csv
import os
import time
from datetime import datetime


# ==========================
# TRON API
# ==========================

API_URL = "https://api.trongrid.io/wallet/getnowblock"
BLOCK_API = "https://api.trongrid.io/wallet/getblockbynum"


# ==========================
# 五玩法配置
# ==========================

GAME_CONFIG = {
    "6s": {
        "name": "6秒哈希",
        "seconds": 6
    },
    "9s": {
        "name": "9秒哈希",
        "seconds": 9
    },
    "15s": {
        "name": "15秒哈希",
        "seconds": 15
    },
    "30s": {
        "name": "30秒哈希",
        "seconds": 30
    },
    "1min": {
        "name": "1分钟哈希",
        "seconds": 60
    }
}


CSV_FILES = {
    "6s": "history_6s.csv",
    "9s": "history_9s.csv",
    "15s": "history_15s.csv",
    "30s": "history_30s.csv",
    "1min": "history_1min.csv"
}


# 每个玩法独立记录
last_blocks = {
    "6s": None,
    "9s": None,
    "15s": None,
    "30s": None,
    "1min": None
}


# ==========================
# 获取最新区块
# ==========================

def get_now_block():

    try:
        r = requests.get(
            API_URL,
            timeout=10
        )

        data = r.json()

        height = data["block_header"]["raw_data"]["number"]
        block_hash = data["blockID"]

        return height, block_hash


    except Exception as e:

        print(
            "[TRON] 获取最新区块失败:",
            e
        )

        return None, None



# ==========================
# 按高度获取区块Hash
# ==========================

def get_block_hash(height):

    try:

        payload = {
            "num": height
        }

        r = requests.post(
            BLOCK_API,
            json=payload,
            timeout=10
        )

        data = r.json()

        return data.get(
            "blockID"
        )


    except Exception as e:

        print(
            f"[TRON] 获取区块 {height}失败:",
            e
        )

        return None



# ==========================
# Hash分析
# ==========================

def analyze_hash(block_hash):

    tail6 = block_hash[-6:]


    number = 0

    for c in reversed(block_hash):

        if c.isdigit():

            number = int(c)
            break


    odd_even = (
        "单"
        if number % 2
        else "双"
    )


    big_small = (
        "大"
        if number >= 5
        else "小"
    )


    return (
        tail6,
        number,
        odd_even,
        big_small
    )



# ==========================
# 初始化CSV
# ==========================

def init_csv(game):

    filename = CSV_FILES[game]


    if not os.path.exists(filename):

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:


            writer = csv.writer(f)


            writer.writerow(
                [
                    "时间",
                    "区块高度",
                    "Hash",
                    "Hash尾6",
                    "尾数",
                    "单双",
                    "大小"
                ]
            )

 # ==========================
# 保存数据
# ==========================

def save_data(
    game,
    height,
    block_hash,
    tail6,
    number,
    odd_even,
    big_small
):

    filename = CSV_FILES[game]


    with open(
        filename,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:


        writer = csv.writer(f)


        writer.writerow(
            [
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                height,
                block_hash,
                tail6,
                number,
                odd_even,
                big_small
            ]
        )



# ==========================
# 根据玩法获取开奖区块
# ==========================

def get_block_time(height):

    try:

        payload = {
            "num": height
        }

        r = requests.post(
            BLOCK_API,
            json=payload,
            timeout=10
        )

        data = r.json()

        timestamp = (
            data["block_header"]
            ["raw_data"]
            ["timestamp"]
        )

        return timestamp // 1000


    except Exception:

        return None



def get_game_block(game, current_height):

    seconds = GAME_CONFIG[game]["seconds"]

    # 根据周期估算区块数量
    block_count = max(1, round(seconds / 3))

    target_height = current_height - block_count


    # 避免几个玩法抢同一区块
    if game == "6s":
        target_height -= 0

    elif game == "9s":
        target_height -= 1

    elif game == "15s":
        target_height -= 2

    elif game == "30s":
        target_height -= 3

    elif game == "1min":
        target_height -= 5


    block_hash = get_block_hash(
        target_height
    )


    if block_hash:

        return (
            target_height,
            block_hash
        )


    return (
        None,
        None
    )


def run_game(game):

    current_height, _ = get_now_block()

    if current_height is None:
        return


    height, block_hash = get_game_block(
        game,
        current_height
    )


    if height is None or block_hash is None:
        return


    # 防止重复记录
    if last_blocks[game] == height:
        return


    tail6, number, odd_even, big_small = analyze_hash(
        block_hash
    )


    print(
        f"[{game}] "
        f"区块:{height} "
        f"尾数:{number} "
        f"{odd_even}{big_small}"
    )


    save_data(
        game,
        height,
        block_hash,
        tail6,
        number,
        odd_even,
        big_small
    )


    last_blocks[game] = height

def main():

    for game in CSV_FILES:
        init_csv(game)

        print(
            f"[初始化] {game} -> {CSV_FILES[game]}"
        )


    print("==============================")
    print("TRON 五玩法实时采集启动")
    print("==============================")

    print(
        "6秒 | 9秒 | 15秒 | 30秒 | 1分钟"
    )


    while True:

        for game in GAME_CONFIG:

            run_game(game)


        time.sleep(3)


if __name__ == "__main__":

    main()           