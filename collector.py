
import requests
import csv
import os
import time
import threading
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
        "seconds": 6,
        "suffix": 80,           # 保留：旧版尾数匹配（已弃用）
        "block_interval": 2     # 新增：每2个区块开奖
    },
    "9s": {
        "name": "9秒哈希",
        "seconds": 9,
        "suffix": 60,
        "block_interval": 3     # 每3个区块开奖
    },
    "15s": {
        "name": "15秒哈希",
        "seconds": 15,
        "suffix": 40,
        "block_interval": 5     # 每5个区块开奖
    },
    "30s": {
        "name": "30秒哈希",
        "seconds": 30,
        "suffix": 20,
        "block_interval": 10    # 每10个区块开奖
    },
    "1min": {
        "name": "1分钟哈希",
        "seconds": 60,
        "suffix": 0,
        "block_interval": 20    # 每20个区块开奖
    }
}


CSV_FILES = {
    "6s": "/data/history_6s.csv",
    "9s": "/data/history_9s.csv",
    "15s": "/data/history_15s.csv",
    "30s": "/data/history_30s.csv",
    "1min": "/data/history_1min.csv"
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
# 【新增】每个玩法独立锁（解决全局锁导致6s/9s/15s互相卡死漏单）
# ==========================
game_locks = {game: threading.Lock() for game in GAME_CONFIG}


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

    # 【修改1】在 open 里加上了 buffering=1
    with open(
        filename,
        "a",
        newline="",
        encoding="utf-8",
        buffering=1
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
        # 【修改2】在写入后加上了 f.flush()
        f.flush()
# ==========================
# 根据玩法和尾数获取开奖区块（旧版尾数匹配，已弃用，保留供参考）
# ==========================

def find_target_block(current_height, target_suffix):
    """旧版尾数匹配逻辑（已弃用）"""
    for offset in range(300):
        check_height = current_height - offset
        if check_height < 0:
            break
        if check_height % 20 == target_suffix:
            block_hash = get_block_hash(check_height)
            if block_hash:
                return check_height, block_hash
    return None, None


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


# ==========================
# 【核心修改】根据区块高度精确计算目标区块
# ==========================

def get_game_block(game, current_height):
    """
    根据区块高度直接计算目标区块，精确对齐平台开奖。
    不再使用错误的尾数匹配，改用 interval 取模。
    """
    interval = GAME_CONFIG[game]["block_interval"]
    # 找到当前高度之前（含当前）最接近的 interval 的倍数
    # 例：current=10001, interval=2 -> target=10000
    # 例：current=10001, interval=20 -> target=10000
    # 【修复】主动加一个周期，直接抓取当前正在进行的下一期区块
    # 避免因为向下取整导致慢一期
    target_height = ((current_height // interval) + 1) * interval
    block_hash = get_block_hash(target_height)
    if block_hash:
        return target_height, block_hash
    return None, None


# ==========================
# 【优化】批量处理所有游戏（复用同一次区块查询）
# ==========================
def run_all_games():
    # 只请求一次最新区块，供所有游戏复用
    current_height, _ = get_now_block()
    if current_height is None:
        return

    for game in GAME_CONFIG:
        try:
            with game_locks[game]:
                interval = GAME_CONFIG[game]["block_interval"]
                # 每个游戏根据自己的 interval 计算目标区块
                target_height = (current_height // interval) * interval
                
                # 防止重复记录
                if last_blocks[game] == target_height:
                    continue

                block_hash = get_block_hash(target_height)
                if block_hash is None:
                    continue

                tail6, number, odd_even, big_small = analyze_hash(block_hash)

                print(f"[{game}] 区块:{target_height} 尾数:{number} {odd_even}{big_small}")

                save_data(game, target_height, block_hash, tail6, number, odd_even, big_small)
                last_blocks[game] = target_height
        except Exception as e:
            print(f"[错误] {game} 采集异常: {e}")
def main():
    # 【新增】启动时自动与波场区块同步，防止重启后期号错位
    print("[初始化] 正在与波场区块同步...")
    sync_height, sync_hash = get_now_block()
    if sync_height is None:
        print("[错误] 无法连接到波场节点，请检查网络")
        return
    print(f"[同步] 当前区块高度: {sync_height}")
    print(f"[同步] 区块Hash: {sync_hash}")
    print("=" * 40)

    for game in CSV_FILES:
        init_csv(game)
        print(
            f"[初始化] {game} -> {CSV_FILES[game]}"
        )

    print("=" * 40)
    print("TRON 五玩法实时采集启动")
    print("=" * 40)

    print("规则：")
    print("  6秒   → 每2个区块开奖")
    print("  9秒   → 每3个区块开奖")
    print("  15秒  → 每5个区块开奖")
    print("  30秒  → 每10个区块开奖")
    print("  1分钟 → 每20个区块开奖")

        # 【核心修改】启动时自动追平最新区块
    print("[自动追平] 正在计算当前最新期号...")
    for game in GAME_CONFIG:
        interval = GAME_CONFIG[game]["block_interval"]
        # 根据当前最新区块高度，直接算出当前应该开到了第几期
        # 这样程序一启动，就跳过所有旧数据，直接从最新一期开始采集
        last_blocks[game] = (sync_height // interval) * interval
        print(f"[自动追平] {game} 已对齐到区块: {last_blocks[game]}")
    print("=" * 40)

    while True:
        try:
            # 调用新的批量处理函数
            run_all_games()
        except Exception as e:
            print(f"[严重错误] 主循环异常: {e}")
        
        # 优化：因为减少了请求次数，可以把休眠时间缩短到 1 秒
        time.sleep(1)


if __name__ == "__main__":

    main()
