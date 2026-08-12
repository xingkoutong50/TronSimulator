import json
import os
import csv
import time
import threading
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from datetime import datetime
# 第三方库
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
PORT = int(os.environ.get("PORT", 8080))

# ========== TRON API ==========
TRON_API = "https://api.trongrid.io/wallet/getnowblock"
HISTORY_API = "https://api.trongrid.io/wallet/getblockbynum"

# ========== 玩法配置 ==========
GAMES = ["6s", "9s", "15s", "1min", "30s"]

GAME_DISPLAY_NAMES = {
    "6s": "6秒哈希",
    "9s": "9秒哈希",
    "15s": "15秒哈希",
    "1min": "1分钟哈希",
    "30s": "30秒哈希"
}

GAME_SUFFIX = {
    "6s": 2,
    "9s": 3,
    "15s": 5,
    "30s": 10,
    "1min": 20
}

GAME_DATA_FILES = {
    "6s": "/data/history_6s.csv",
    "9s": "/data/history_9s.csv",
    "15s": "/data/history_15s.csv",
    "1min": "/data/history_1min.csv",
    "30s": "/data/history_30s.csv",
}
PREDICT_FILE = "block_prediction_log_v67.csv"

file_lock = threading.Lock()

# ========== 缓存系统 ==========
class DataCache:
    def __init__(self, ttl_seconds=8):
        self.cache = {}
        self.ttl = ttl_seconds
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return data
                else:
                    del self.cache[key]
            return None
    
    def set(self, key, data):
        with self.lock:
            self.cache[key] = (data, time.time())
    
    def clear(self):
        with self.lock:
            self.cache.clear()

cache = DataCache(ttl_seconds=3600)

# ========== 文件变动监控器 ==========
class CSVFileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # 只处理 CSV 文件的修改事件
        if event.is_directory:
            return
        if event.src_path.endswith('.csv'):
            print(f"[监控] 检测到文件变动: {event.src_path}，正在清空缓存...")
            cache.clear() # 核心操作：清空缓存，强制下次请求时重新读取文件

def start_file_watcher():
    # 监控当前目录下的所有文件变动
    event_handler = CSVFileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    print("[监控] 已启动文件变动监控...")
    return observer

# ========== TRON 链上时间缓存 ==========
_tron_time_cache = None
_tron_time_cache_time = 0

# ========== 获取倒计时 ==========
def get_countdown(game):
    if game == "6s":
        total = 6
    elif game == "9s":
        total = 9
    elif game == "15s":
        total = 15
    elif game == "30s":
        total = 30
    elif game == "1min":
        total = 60
    else:
        total = 30

    tron_time = get_tron_timestamp()
    if tron_time is None:
        tron_time = int(time.time())

    current = tron_time % total
    remaining = total - current
    if remaining == 0:
        remaining = total

    return remaining, total, tron_time
def get_tron_timestamp():
    """获取当前 TRON 区块链时间戳（秒级），缓存 2 秒减少 API 调用"""
    global _tron_time_cache, _tron_time_cache_time
    now = time.time()
    if _tron_time_cache is not None and now - _tron_time_cache_time < 2:
        return int(_tron_time_cache + (now - _tron_time_cache_time))
    for retry in range(3):
        try:
            r = requests.get(TRON_API, timeout=10)
            if r.status_code == 200:
                data = r.json()
                tron_ts = int(data.get("timestamp", 0) // 1000)
                _tron_time_cache = tron_ts
                _tron_time_cache_time = now
                return tron_ts
        except Exception:
            pass
        time.sleep(1)
    return None

# ========== 获取指定区块 ==========
def get_block_by_number(height):
    for retry in range(3):
        try:
            payload = {"num": height}
            r = requests.post(HISTORY_API, json=payload, timeout=10)
            if r.status_code != 200:
                time.sleep(2)
                continue
            data = r.json()
            block_hash = data.get("blockID", "")
            if block_hash:
                return block_hash
            time.sleep(2)
        except:
            time.sleep(2)
    return None

def find_target_block(current_height, target_suffix):
    for offset in range(500):
        check_height = current_height - offset
        if check_height < 0:
            break
        if check_height % 20 == target_suffix:
            block_hash = get_block_by_number(check_height)
            if block_hash:
                return check_height, block_hash
    return None, None

def fetch_game_block(game):
    target_suffix = GAME_SUFFIX.get(game, 0)
    
    for retry in range(3):
        try:
            r = requests.get(TRON_API, timeout=10)
            if r.status_code != 200:
                time.sleep(2)
                continue
            
            data = r.json()
            if "block_header" not in data:
                time.sleep(2)
                continue
            
            current_height = data["block_header"]["raw_data"]["number"]
            target_height, block_hash = find_target_block(current_height, target_suffix)
            if target_height is None or block_hash is None:
                return None
            
            hash6 = block_hash[-6:]
            last_num = None
            for c in reversed(block_hash):
                if c.isdigit():
                    last_num = int(c)
                    break
            if last_num is None:
                last_num = 0
            
            odd_even = "单" if last_num % 2 == 1 else "双"
            size = "大" if last_num >= 5 else "小"
            
            return {
                "block": str(target_height),
                "hash6": hash6,
                "tail": str(last_num),
                "result": odd_even,
                "size": size,
                "hash": block_hash
            }
        except:
            time.sleep(2)
    
    return None

# ========== 加载数据 ==========

def load_realtime_from_csv(game):

    filename = f"/data/history_{game}.csv"

    cache_key = f"realtime_{game}"

    cached = cache.get(cache_key)

    if cached is not None:
        return cached


    data = []


    if os.path.exists(filename):
        try:
            # 核心修改：使用 'r' 模式打开，并强制刷新文件指针
            with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                # 确保每次读取都从文件最新位置开始
                f.seek(0, os.SEEK_END) 
                f.seek(0, os.SEEK_SET)
                
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) < 7:
                        continue
                    try:
                        data.append({
                            "block": row[1],
                            "hash6": row[3],
                            "tail": row[4],
                            "result": row[5],
                            "size": row[6],
                        })
                    except:
                        continue
        except:
            pass


    # 只使用 collector.py 生成的数据
    # 不再连接TRON接口补数据



    if len(data) > 500:

        data = data[-100:]


    cache.set(
        cache_key,
        data
    )


    return data

def load_predict_logs():
    if not os.path.exists(PREDICT_FILE):
        return {}
    
    result = defaultdict(list)
    try:
        with open(PREDICT_FILE, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                game = row.get("game", "").strip()
                open_block = row.get("open_block", "").strip()
                actual = row.get("actual", "").strip()
                predict = row.get("predict", "").strip()
                result_status = row.get("result", "").strip()
                log_time = row.get("time", "").strip()
                
                if not game or not open_block:
                    continue
                
                result[game].append({
                    "time": log_time,
                    "open_block": open_block,
                    "actual": actual,
                    "predict": predict,
                    "result": result_status,
                })
    except:
        pass
    
    return dict(result)

def load_game_history(game):
    filename = GAME_DATA_FILES.get(game)
    cache_key = f"game_history_{game}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    data = []
    if not os.path.exists(filename):
        return data
    
    try:
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) < 5:
                    continue
                try:
                    tail = int(row[4])
                    data.append({
                        "block": row[1],
                        "hash6": row[3],
                        "tail": str(tail),
                        "result": "单" if tail % 2 else "双",
                        "size": "大" if tail >= 5 else "小",
                    })
                except:
                    continue
    except:
        pass
    
    if len(data) > 500:
        data = data[-10000:]
    cache.set(cache_key, data)
    return data

def realtime_predict(block_hash, game):

    if not block_hash:
        return {
            "predict": "-",
            "model": "-",
            "predict_block": "-"
        }

    try:
        current_block = int(block_hash)

        suffix = GAME_SUFFIX.get(game, 0)

        # 限制搜索范围，防止死循环
        next_block = current_block + 1

        count = 0

        while next_block % suffix != 0 and count < 20:
            next_block += 1
            count += 1

        predict_block = str(next_block)

    except Exception:

        predict_block = "-"


    # 根据区块hash最后数字预测单双

    last_num = None

    for c in reversed(str(block_hash)):

        if c.isdigit():

            last_num = int(c)

            break


    if last_num is None:

        last_num = 0


    predict = "单" if last_num % 2 else "双"


    return {

        "predict": predict,

        "model": "Hash末位",

        "predict_block": predict_block,

        "last_num": last_num

    }


def choose_model(data):
    best = None
    for length in [3, 2, 1]:
        table = defaultdict(lambda: {"单": 0, "双": 0})
        for i in range(len(data) - length):
            key = "".join(x["tail"] for x in data[i:i+length])
            real = data[i+length]["result"]
            table[key][real] += 1
        key = "".join(x["tail"] for x in data[-length:])
        if key not in table:
            continue
        s = table[key]["单"]
        d = table[key]["双"]
        total = s + d
        if total < 5:
            continue
        predict = "单" if s > d else "双"
        rate = max(s, d) / total * 100
        score = rate * (total / (total + 10))
        item = {"model": f"Hash {length}位", "predict": predict, "rate": round(rate, 2), "score": round(score, 2)}
        if best is None or score > best["score"]:
            best = item
    if best:
        return best
    return {"model": "默认", "predict": "双", "rate": 50, "score": 0}    

def calc_stat_from_logs(game_logs):
    if not game_logs:
        return {
            "total": 0,
            "hits": 0,
            "misses": 0,
            "hit_rate": 0,
            "max_win": 0,
            "max_lose": 0,
            "current_status": "无"
        }
    
    total = len(game_logs)
    hits = sum(1 for log in game_logs if log["result"] == "命中")
    misses = total - hits
    hit_rate = round(hits / total * 100, 1) if total > 0 else 0
    
    max_win = 0
    max_lose = 0
    streak = 0
    streak_type = None
    
    for log in game_logs:
        if log["result"] == "命中":
            if streak_type == "win":
                streak += 1
            else:
                streak = 1
                streak_type = "win"
            if streak > max_win:
                max_win = streak
        else:
            if streak_type == "lose":
                streak += 1
            else:
                streak = 1
                streak_type = "lose"
            if streak > max_lose:
                max_lose = streak
    
    current_status = "无"
    if game_logs:
        current_streak = 0
        for log in reversed(game_logs):
            if log["result"] == "命中":
                current_streak += 1
            else:
                break
        if current_streak > 0:
            current_status = f"中{current_streak}连"
        else:
            current_streak = 0
            for log in reversed(game_logs):
                if log["result"] == "错误":
                    current_streak += 1
                else:
                    break
            if current_streak > 0:
                current_status = f"挂{current_streak}连"
    
    return {
        "total": total,
        "hits": hits,
        "misses": misses,
        "hit_rate": hit_rate,
        "max_win": max_win,
        "max_lose": max_lose,
        "current_status": current_status
    }

# ========== 采集器配置 ==========
API_URL = "https://api.trongrid.io/wallet/getnowblock"
BLOCK_API = "https://api.trongrid.io/wallet/getblockbynum"

GAME_CONFIG = {
    "6s": {"block_interval": 2},
    "9s": {"block_interval": 3},
    "15s": {"block_interval": 5},
    "30s": {"block_interval": 10},
    "1min": {"block_interval": 20},
}

collector_csv_files = {
    "6s": "/data/history_6s.csv",
    "9s": "/data/history_9s.csv",
    "15s": "/data/history_15s.csv",
    "30s": "/data/history_30s.csv",
    "1min": "/data/history_1min.csv",
}

collector_last_blocks = {g: None for g in GAMES}
collector_locks = {g: threading.Lock() for g in GAMES}

def collector_get_now_block():
    try:
        r = requests.get(API_URL, timeout=10)
        data = r.json()
        return data["block_header"]["raw_data"]["number"], data["blockID"]
    except Exception as e:
        print(f"[TRON] 获取最新区块失败: {e}")
        return None, None

def collector_get_block_hash(height):
    try:
        r = requests.post(BLOCK_API, json={"num": height}, timeout=10)
        return r.json().get("blockID")
    except Exception as e:
        print(f"[TRON] 获取区块 {height} 失败: {e}")
        return None

def collector_analyze_hash(block_hash):
    tail6 = block_hash[-6:]
    number = 0
    for c in reversed(block_hash):
        if c.isdigit():
            number = int(c)
            break
    odd_even = "单" if number % 2 else "双"
    big_small = "大" if number >= 5 else "小"
    return tail6, number, odd_even, big_small

def collector_init_csv(game):
    filename = collector_csv_files[game]
    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["时间", "区块高度", "Hash", "Hash尾6", "尾数", "单双", "大小"])

def collector_save_data(game, height, block_hash, tail6, number, odd_even, big_small):
    filename = collector_csv_files[game]
    with open(filename, "a", newline="", encoding="utf-8", buffering=1) as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), height, block_hash, tail6, number, odd_even, big_small])
        f.flush()

def collector_run_all_games():
    current_height, _ = collector_get_now_block()
    if current_height is None:
        return
    for game in GAMES:
        try:
            with collector_locks[game]:
                interval = GAME_CONFIG[game]["block_interval"]
                target_height = (current_height // interval) * interval
                if collector_last_blocks[game] == target_height:
                    continue
                block_hash = collector_get_block_hash(target_height)
                if block_hash is None:
                    continue
                tail6, number, odd_even, big_small = collector_analyze_hash(block_hash)
                print(f"[采集] {game} 区块:{target_height} 尾数:{number} {odd_even}{big_small}")
                collector_save_data(game, target_height, block_hash, tail6, number, odd_even, big_small)
                collector_last_blocks[game] = target_height
        except Exception as e:
            print(f"[采集错误] {game}: {e}")

def collector_main():
    print("[采集] 正在初始化...")
    sync_height, _ = collector_get_now_block()
    if sync_height is None:
        print("[采集错误] 无法连接TRON节点")
        return
    for game in GAMES:
        collector_init_csv(game)
        interval = GAME_CONFIG[game]["block_interval"]
        collector_last_blocks[game] = (sync_height // interval) * interval
        print(f"[采集] {game} 已对齐到区块: {collector_last_blocks[game]}")
    print("[采集] 启动完成")
    while True:
        try:
            collector_run_all_games()
        except Exception as e:
            print(f"[采集严重错误] {e}")
        time.sleep(1)




def preload_all_data():
    print("[预加载] 开始加载所有数据...")
    for g in GAMES:
        load_realtime_from_csv(g)
        load_game_history(g)
    load_predict_logs()
    
    # 预热：提前计算统计数据和预测结果
    print("[预热] 正在预计算统计数据...")
    for g in GAMES:
        history_data = load_game_history(g)
        stat_logs = []
        for i in range(50, len(history_data)):
            slice_data = history_data[max(0, i-200):i]
            model = choose_model(slice_data)
            actual = history_data[i]["result"]
            stat_logs.append({
                "result": "命中" if actual == model["predict"] else "错误"
            })
        cache.set(f"precalc_stats_{g}", calc_stat_from_logs(stat_logs))
    print("[预热] 完成！")

def background_refresh():
    while True:
        time.sleep(5)
        try:
            for g in GAMES:
                cache.cache.pop(f"realtime_{g}", None)
                cache.cache.pop(f"game_history_{g}", None)
                load_realtime_from_csv(g)
                load_game_history(g)
        except:
            pass

# ========== Handler ==========
class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # 快速响应健康检查
        if self.path == '/health':
            if os.path.exists("/tmp/ready"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            else:
                self.send_response(503)
                self.end_headers()
            return
        if self.path == '/api/time':
            tron_ts = get_tron_timestamp()
            if tron_ts is None:
                tron_ts = int(time.time())
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"tron_ts": {tron_ts}}}'.encode("utf-8"))
            return

        # --- 新增：处理前端的数据自动刷新请求 ---
        if self.path == '/api/data':
            all_data = {}
            for g in GAMES:
                all_data[g] = load_realtime_from_csv(g)
            tron_ts = get_tron_timestamp() or int(time.time())
            
            # 重新生成实时数据 HTML
            realtime_html = self.build_realtime_html(all_data, tron_ts)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            # 将 HTML 包装成 JSON 返回
            response = json.dumps({"html": realtime_html})
            self.wfile.write(response.encode("utf-8"))
            return
        # --- 新增结束 ---

        # 下面是原有的网页渲染逻辑...
        try:
            all_data = {}
            # ... (后面保持你原有的代码不变)
            all_stats = {}

            print("B1读取预测日志")

            predict_logs = load_predict_logs()


            print("B2开始读取CSV")


            for g in GAMES:

                print("读取:", g)

                data = load_realtime_from_csv(g)

                print("完成:", g)

                all_data[g] = data

                all_stats[g] = cache.get(f"precalc_stats_{g}") or {"total": 0, "hits": 0, "misses": 0, "hit_rate": 0, "max_win": 0, "max_lose": 0, "current_status": "无"}

            print("C开始生成实时页面")

            # 获取 TRON 链上时间，传递给前端
            tron_ts = get_tron_timestamp()
            if tron_ts is None:
                tron_ts = int(time.time())

            realtime_html = self.build_realtime_html(all_data, tron_ts)

            stats_html = self.build_stats_html(all_stats)

            streak_html = self.build_streak_html(predict_logs)

            trend_history_html = self.build_trend_with_history_html(all_data, predict_logs)

            print("D开始拼接HTML")


            html = self.build_full_page(
                realtime_html,
                stats_html,
                streak_html,
                trend_history_html,
                tron_ts
            )


            print("HTML发送完成")


            self.send_response(200)

            self.send_header(
                "Cache-Control",
                "no-cache"
            )

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.end_headers()


            self.wfile.write(
                html.encode("utf-8")
            )


        except Exception as e:

            print(f"[错误] {e}")

            self.send_error(
                500,
                f"Internal Server Error: {e}"
            )


    def build_realtime_html(self, all_data, tron_ts):
        html = ""
        for g in GAMES:
            data = all_data.get(g, [])
            latest = data[-1] if data else {}
            display_name = GAME_DISPLAY_NAMES.get(g, g)

                       # --- 1. 确定总时长 ---
            if g == "6s":
                total = 6
            elif g == "9s":
                total = 9
            elif g == "15s":
                total = 15
            elif g == "30s":
                total = 30
            elif g == "1min":
                total = 60
            else:
                total = 30

            # --- 2. 计算剩余时间 ---
            current = tron_ts % total
            remaining = total - current
            if remaining == 0:
                remaining = total

            # --- 3. 计算进度条 ---
            progress = ((total - remaining) / total) * 100

            # --- 4. 获取其他数据 ---
            current_block = latest.get("block", "-")
            hash6 = latest.get("hash6", "-")
            tail = latest.get("tail", "-")
            predict_info = realtime_predict(current_block, g)
            predict = predict_info.get("predict", "-")
            predict_block = predict_info.get("predict_block", "-")

            # --- 5. 生成趋势图数据 ---
            trend_data = data[-30:] if len(data) >= 30 else data
            trend_dots = ""
            odd_count = 0
            even_count = 0
            for d in trend_data:
                if d["result"] == "单":
                    trend_dots += '<span class="trend-dot-platform odd">单</span>'
                    odd_count += 1
                else:
                    trend_dots += '<span class="trend-dot-platform even">双</span>'
                    even_count += 1

            predict_color = "#ff4444" if predict == "单" else "#44bb88"
            suffix_info = f"尾数 {GAME_SUFFIX[g]}"

            # --- 6. 关键修改：将倒计时部分移出 .realtime-item ---
            html += f'''
            <div class="game-card">
                <div class="realtime-header">
                    <span class="play-name">{display_name}</span>
                    <!-- 倒计时部分：独立于 .realtime-item，不会被自动刷新覆盖 -->
                    <span class="countdown-badge">
                        ⏱ <span class="countdown-number" id="cd-{g}">{remaining}</span> 秒
                    </span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="pg-{g}" style="width:{progress}%;"></div>
                </div>
                
                <!-- 实时数据部分：这才是需要自动刷新的区域 -->
                <div class="realtime-item">
                    <div class="block-display">
                        <div class="block-left">
                            <div class="block-label">📌 已开奖 ({suffix_info})</div>
                            <div class="block-number">{current_block}</div>
                            <div class="block-detail">验证 {tail}</div>
                        </div>
                        <div class="block-right">
                            <div class="block-label">🎯 下注</div>
                            <div class="block-number">{predict_block}</div>
                            <div class="block-detail">...{hash6}</div>
                            <div class="block-result" style="color:{predict_color};font-size:1.8rem;font-weight:900;text-shadow:0 0 20px {predict_color}40;">预测 {predict}</div>
                        </div>
                    </div>
                    <div class="trend-section">
                        <div class="trend-header">
                            <span style="font-size:0.7rem;font-weight:600;color:#555;">📊 往期开奖</span>
                            <span style="font-size:0.7rem;font-weight:600;color:#888;">单 {odd_count} 双 {even_count}</span>
                        </div>
                        <div class="trend-dots">{trend_dots if trend_dots else '<span style="color:#999;font-size:0.7rem;">暂无数据</span>'}</div>
                    </div>
                </div>
            </div>
            '''
        return html
    def build_stats_html(self, all_stats):
        html = ""
        for g in GAMES:
            stat = all_stats.get(g, {})
            display_name = GAME_DISPLAY_NAMES.get(g, g)
            html += f'''
            <div class="cardHover stats-item">
                <div class="play-name">{display_name}</div>
                <div>总次数: {stat.get("total", 0)}</div>
                <div>命中: {stat.get("hits", 0)} | 错误: {stat.get("misses", 0)}</div>
                <div style="font-size:1.2rem;font-weight:700;color:#c44545;margin:4px 0;">{stat.get("hit_rate", 0)}%</div>
                <div>最大连中: {stat.get("max_win", 0)} | 最大连挂: {stat.get("max_lose", 0)}</div>
                <div class="status">当前: {stat.get("current_status", "无")}</div>
            </div>'''
        return html

    def build_streak_html(self, predict_logs):
        html = ""
        for g in GAMES:
            game_logs = predict_logs.get(g, [])
            display_name = GAME_DISPLAY_NAMES.get(g, g)
            recent = game_logs[-30:] if len(game_logs) >= 30 else game_logs
            dots = ""
            for log in recent:
                if log["result"] == "命中":
                    dots += '<span class="streak-dot hit">√</span>'
                elif log["result"] == "错误":
                    dots += '<span class="streak-dot miss">×</span>'
                else:
                    dots += '<span class="streak-dot" style="background:#f0f0f0;color:#999;">-</span>'
            html += f'''
            <div class="streak-item">
                <div class="play-name">{display_name}</div>
                <div class="streak-dots">{dots}</div>
            </div>'''
        return html

    def build_trend_with_history_html(self, all_data, predict_logs):
        html = ""
        for g in GAMES:
            history_data = load_game_history(g)
            display_name = GAME_DISPLAY_NAMES.get(g, g)
            
            trend50 = history_data[-50:] if len(history_data) >= 50 else history_data
            dots = ""
            odd_count = 0
            even_count = 0
            for d in trend50:
                if d["result"] == "单":
                    dots += '<span class="trend-dot odd">单</span>'
                    odd_count += 1
                else:
                    dots += '<span class="trend-dot even">双</span>'
                    even_count += 1
            total = odd_count + even_count
            odd_pct = round(odd_count/total*100) if total > 0 else 0
            even_pct = round(even_count/total*100) if total > 0 else 0
            
            recent_history = list(reversed(history_data[-10000:])) if len(history_data) >= 500 else list(reversed(history_data))
            history_rows = ""
            consecutive_hits = 0
            
            for i, d in enumerate(recent_history):
                block = d.get("block", "-")
                hash6 = d.get("hash6", "-")
                tail = d.get("tail", "-")
                actual = d.get("result", "-")
                size = d.get("size", "-")
                
                idx = len(history_data) - 1 - i
                if idx >= 50:
                    slice_data = history_data[max(0, idx-200):idx]
                    model = choose_model(slice_data)
                    predict = model["predict"]
                    result_status = "命中" if actual == predict else "错误"
                else:
                    predict = "-"
                    result_status = ""
                
                if result_status == "命中":
                    consecutive_hits += 1
                    if consecutive_hits >= 3:
                        size_val = min(1.2 + consecutive_hits * 0.08, 2.5)
                        result_display = f'<span style="color:#2e7d32;font-weight:900;font-size:{size_val}rem;display:inline-block;animation:pulse 1.2s ease-in-out infinite;">中{consecutive_hits}连✅</span>'
                    else:
                        result_display = '<span style="color:#2e7d32;font-weight:700;">√ 中</span>'
                elif result_status == "错误":
                    consecutive_hits = 0
                    result_display = '<span style="color:#c62828;font-weight:700;">× 挂</span>'
                else:
                    consecutive_hits = 0
                    result_display = '<span style="color:#999;">-</span>'
                    predict = "-"
                
                history_rows += f'''
                <tr>
                    <td style="font-size:.75rem;padding:4px 6px;text-align:center;">-</td>
                    <td style="font-size:.75rem;padding:4px 6px;text-align:center;font-weight:600;">{block}</td>
                    <td style="font-size:.75rem;padding:4px 6px;text-align:center;font-weight:600;color:#1a3a5c;">{hash6}</td>
                    <td style="font-size:.75rem;padding:4px 6px;text-align:center;font-weight:600;color:#1a3a5c;">{actual}</td>
                    <td style="font-size:.75rem;padding:4px 6px;text-align:center;font-weight:600;color:#1a3a5c;">{size}</td>
                    <td style="font-size:.75rem;padding:4px 6px;text-align:center;font-weight:600;color:#c44545;">{predict}</td>
                    <td style="font-size:.75rem;padding:4px 6px;text-align:center;">{result_display}</td>
                </tr>'''
            
            html += f'''
            <div class="trend-item" style="display:flex;flex-direction:column;background:#fafbfc;border:1px solid #e8ecf1;border-radius:8px;padding:12px;">
                <div class="play-name" style="font-weight:700;font-size:1.2rem;color:#1a3a5c;margin-bottom:6px;text-align:center;">{display_name}</div>
                <div class="trend-dots" style="display:flex;flex-wrap:wrap;gap:3px;justify-content:center;margin:6px 0;">{dots}</div>
                <div class="trend-count" style="font-size:.8rem;color:#666;text-align:center;margin-bottom:8px;font-weight:600;">单: {odd_count}次({odd_pct}%) | 双: {even_count}次({even_pct}%)</div>
                
                <div style="border-top:2px solid #e8ecf1;padding-top:8px;margin-top:4px;">
                    <div style="font-size:.8rem;font-weight:700;color:#1a3a5c;margin-bottom:6px;text-align:center;">📋 {display_name} 历史验证（最近{len(recent_history)}期）</div>
                    <div style="overflow-x:auto;">
                        <table style="width:100%;border-collapse:collapse;font-size:.75rem;">
                            <thead>
                                <tr style="background:#e8ecf1;position:sticky;top:0;z-index:1;">
                                    <th style="padding:4px 6px;text-align:center;font-size:.65rem;font-weight:700;color:#1a3a5c;">时间</th>
                                    <th style="padding:4px 6px;text-align:center;font-size:.65rem;font-weight:700;color:#1a3a5c;">区块</th>
                                    <th style="padding:4px 6px;text-align:center;font-size:.65rem;font-weight:700;color:#1a3a5c;">Hash尾6</th>
                                    <th style="padding:4px 6px;text-align:center;font-size:.65rem;font-weight:700;color:#1a3a5c;">开奖</th>
                                    <th style="padding:4px 6px;text-align:center;font-size:.65rem;font-weight:700;color:#1a3a5c;">大小</th>
                                    <th style="padding:4px 6px;text-align:center;font-size:.65rem;font-weight:700;color:#1a3a5c;">预测</th>
                                    <th style="padding:4px 6px;text-align:center;font-size:.65rem;font-weight:700;color:#1a3a5c;">结果</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history_rows if history_rows else '<tr><td colspan="7" style="text-align:center;color:#999;font-size:.75rem;padding:12px;">暂无数据</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>'''
        return html
    def build_full_page(self, realtime_html, stats_html, streak_html, trend_history_html, tron_ts):
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=yes">
<title>TRON 智能预测 · 数据分析后台</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI','PingFang SC',Arial,sans-serif;background:linear-gradient(135deg,#f5f7fa,#e8ecf1);min-height:100vh;padding:16px}}
.card{{background:#fff;border-radius:12px;padding:16px;margin-bottom:14px;box-shadow:0 2px 12px rgba(0,0,0,.06);border:1px solid #e8e8e8}}
.header{{background:linear-gradient(135deg,#1a3a5c,#0f2844);color:white;border:none;box-shadow:0 4px 16px rgba(18,52,97,.2);position:relative;overflow:hidden}}
.header::after{{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(45deg,transparent 40%,rgba(255,255,255,.05) 50%,transparent 60%);animation:scan 3s infinite}}
@keyframes scan{{0%{{transform:translateX(-100%)}}100%{{transform:translateX(100%)}}}}
.title{{font-size:1.8rem;font-weight:700;letter-spacing:1px;position:relative;z-index:1;}}
.title-text{{color:white;}}
.sub{{font-size:.8rem;opacity:.8;margin-top:6px;position:relative;z-index:1}}
.section{{font-size:.95rem;font-weight:600;color:#1a3a5c;margin-bottom:10px;padding-bottom:8px;border-bottom:2px solid #e8ecf1}}
.cardHover:hover{{transform:translateY(-2px);box-shadow:0 4px 16px rgba(0,0,0,.1)}}

.realtime-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.realtime-item{{background:#fff;border:1px solid #e8ecf1;border-radius:8px;padding:12px;box-shadow:0 1px 4px rgba(0,0,0,.04)}}
.realtime-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}}
.play-name{{font-weight:700;font-size:1rem;color:#1a3a5c}}
.countdown-badge{{font-size:.9rem;color:#c44545;font-weight:700;background:#fce4e4;padding:2px 12px;border-radius:12px}}
.countdown-number{{font-size:1.4rem;color:#c44545;font-weight:900;min-width:24px;display:inline-block;text-align:center}}
.progress-bar{{width:100%;height:3px;background:#e8ecf1;border-radius:2px;margin-bottom:8px;overflow:hidden}}
.progress-fill{{height:100%;background:linear-gradient(90deg,#c44545,#f39c12);border-radius:2px;transition:width 0.3s}}
.block-display{{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px}}
.block-left,.block-right{{background:#f8f9fa;border-radius:6px;padding:8px 8px;text-align:center}}
.block-label{{font-size:.65rem;color:#999;font-weight:600;letter-spacing:.5px}}
.block-number{{font-size:1.1rem;font-weight:700;color:#1a3a5c}}
.block-detail{{font-size:.7rem;color:#888;margin-top:2px}}
.block-result{{font-size:1.8rem;font-weight:900;margin-top:4px;transition:all 0.3s}}
.trend-section{{background:#f8f9fa;border-radius:6px;padding:6px 8px}}
.trend-header{{display:flex;justify-content:space-between;font-size:.7rem;font-weight:600;color:#555;margin-bottom:3px}}
.trend-dots{{display:flex;flex-wrap:wrap;gap:3px;min-height:22px}}
.trend-dot-platform{{width:22px;height:22px;border-radius:4px;font-size:.6rem;display:flex;align-items:center;justify-content:center;font-weight:700}}
.trend-dot-platform.odd{{background:#e3f2fd;color:#1565c0;font-size:.7rem}}
.trend-dot-platform.even{{background:#fce4ec;color:#c62828;font-size:.7rem}}

.stats-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.stats-item{{background:#fafbfc;border:1px solid #e8ecf1;border-radius:8px;padding:14px;text-align:center;font-size:.78rem}}
.stats-item .play-name{{font-weight:700;font-size:.9rem;color:#1a3a5c;margin-bottom:8px}}
.stats-item .status{{font-weight:700;margin-top:6px;font-size:.75rem;color:#f39c12}}

.streak-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.streak-item{{background:#fafbfc;border:1px solid #e8ecf1;border-radius:8px;padding:12px;text-align:center;font-size:.75rem}}
.streak-item .play-name{{font-weight:700;font-size:.85rem;color:#1a3a5c;margin-bottom:6px}}
.streak-dots{{display:flex;flex-wrap:wrap;gap:3px;justify-content:center;margin-top:4px}}
.streak-dot{{width:22px;height:22px;border-radius:4px;font-size:.7rem;display:flex;align-items:center;justify-content:center;font-weight:700}}
.streak-dot.hit{{background:#e8f5e9;color:#2e7d32}}
.streak-dot.miss{{background:#fce4e4;color:#c62828}}

.trend-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.trend-item{{background:#fafbfc;border:1px solid #e8ecf1;border-radius:8px;padding:12px;text-align:center;font-size:.75rem}}
.trend-item .play-name{{font-weight:700;font-size:1.2rem;color:#1a3a5c;margin-bottom:6px}}
.trend-dots{{display:flex;flex-wrap:wrap;gap:3px;justify-content:center;margin:6px 0}}
.trend-dot{{width:22px;height:22px;border-radius:50%;font-size:.6rem;display:flex;align-items:center;justify-content:center;font-weight:700}}
.trend-dot.odd{{background:#e3f2fd;color:#1565c0}}
.trend-dot.even{{background:#fce4ec;color:#c62828}}
.trend-count{{font-size:.8rem;color:#666;text-align:center;margin-bottom:8px;font-weight:600}}

.history-tab-content{{overflow-x:auto}}
.history-tab-content table{{width:100%;border-collapse:collapse;font-size:.75rem}}
.history-tab-content th{{background:#1a3a5c;color:#fff;padding:6px 6px;font-weight:600;text-align:center;font-size:.65rem}}
.history-tab-content td{{padding:6px 6px;text-align:center;border-bottom:1px solid #f0f0f0;font-size:.7rem}}
.hit-cell{{color:#2e7d32;font-weight:700}}
.miss-cell{{color:#c62828;font-weight:700}}

@keyframes pulse{{0%,100%{{transform:scale(1);opacity:1}}50%{{transform:scale(1.15);opacity:.9}}}}
.pulse{{animation:pulse 1.2s ease-in-out infinite;display:inline-block}}

::-webkit-scrollbar{{width:4px;height:4px}}
::-webkit-scrollbar-track{{background:#f1f1f1;border-radius:4px}}
::-webkit-scrollbar-thumb{{background:#c1c1c1;border-radius:4px}}
::-webkit-scrollbar-thumb:hover{{background:#a8a8a8}}

@media(max-width:1200px){{.realtime-grid,.stats-grid,.streak-grid,.trend-grid{{grid-template-columns:repeat(3,1fr)}}}}
@media(max-width:768px){{.realtime-grid,.stats-grid,.streak-grid,.trend-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:480px){{.realtime-grid,.stats-grid,.streak-grid,.trend-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="card header">
    <div class="title">
        <span class="title-text">🔮 TRON 智能预测 · 数据分析后台</span>
    </div>
    <div class="sub">五玩法实时追踪 | 实时哈希预测 | 走势分析 | V7 实时版</div>
</div>

<div class="card">
    <div class="section">📡 实时开奖</div>
    <div class="realtime-grid">{realtime_html}</div>
</div>

<div class="card">
    <div class="section">📊 策略统计</div>
    <div class="stats-grid">{stats_html}</div>
</div>

<div class="card">
    <div class="section">📈 连续走势（√ 命中 / × 错误）</div>
    <div class="streak-grid">{streak_html}</div>
</div>

<div class="card">
    <div class="section">🔴🔵 单双趋势（最近50期）+ 历史验证（最近500期）</div>
    <div class="trend-grid">{trend_history_html}</div>
</div>


            <script>
                // 1. 初始化链上时间偏移量
                var TRON_TIMESTAMP = {tron_ts};
                var PAGE_LOAD_LOCAL = Math.floor(Date.now() / 1000);
                var TRON_OFFSET = TRON_TIMESTAMP - PAGE_LOAD_LOCAL;

                // 2. 每30秒后台校准一次时间，防止本地时间漂移
                setInterval(function() {{
                    fetch('/api/time').then(function(r) {{ return r.json(); }}).then(function(d) {{
                        TRON_OFFSET = d.tron_ts - Math.floor(Date.now() / 1000);
                    }}).catch(function(){{}});
                }}, 30000);

                // 3. 倒计时核心逻辑
                var countdowns = {{
                    "6s": 6,
                    "9s": 9,
                    "15s": 15,
                    "30s": 30,
                    "1min": 60
                }};
    function updateAllCountdowns() {{
        for (const [game, total] of Object.entries(countdowns)) {{
            let el = document.getElementById('cd-' + game);
            if (!el) continue;
            let remaining = parseInt(el.textContent) || total;
            remaining -= 1;
            if (remaining <= 0) {{
                remaining = total;
                setTimeout(function(){{ window.location.reload(); }}, 500);
            }}
            el.textContent = remaining;
            const pg = document.getElementById('pg-' + game);
            if (pg) pg.style.width = ((total - remaining) / total * 100) + '%';
        }}
    }}
                // 4. 立即执行一次，然后每秒更新倒计时
                updateAllCountdowns();
                setInterval(updateAllCountdowns, 1000);
        // 每秒检查新区块，发现后自动刷新
    let lastBlocks = {{}};
    setInterval(function() {{
        fetch('/api/latest').then(r => r.json()).then(d => {{
            let changed = false;
            for (const [game, data] of Object.entries(d)) {{
                if (lastBlocks[game] && lastBlocks[game] !== data.block) {{
                    changed = true;
                }}
                lastBlocks[game] = data.block;
            }}
            if (changed) window.location.reload();
        }}).catch(()=>{{}});
    }}, 1000);
                // 5. 数据自动刷新（只更新数据卡片，绝不碰倒计时）
                function autoRefreshData() {{
                    fetch('/api/data')
                        .then(function(response) {{ return response.json(); }})
                        .then(function(data) {{
                            var tempDiv = document.createElement('div');
                            tempDiv.innerHTML = data.html;
                            
                            var newCards = tempDiv.querySelectorAll('.realtime-item');
                            var oldCards = document.querySelectorAll('.realtime-item');
                            
                            if (newCards.length === oldCards.length) {{
                                for (var i = 0; i < newCards.length; i++) {{
                                    oldCards[i].innerHTML = newCards[i].innerHTML;
                                }}
                            }}
                        }})
                        .catch(function(err) {{ console.log('自动刷新数据失败:', err); }});
                }}
                
                // 每3秒自动获取一次最新数据
                setInterval(autoRefreshData, 3000);
            </script>
    
</script>
</body>
</html>'''

# ========== 工具函数 ==========
def get_color(n):
    colors = ['#3b5d7e','#c44545','#2a7a62','#b17d3a','#6d4f8a','#c0606a','#3e7a8a','#b35d5d','#4f7a5f','#8f6b4b']
    return colors[int(n) % 10] if n else colors[0]

def make_ball(n, size=32, animated=True):
    if n == "-" or n is None:
        return '<span style="color:#999;">-</span>'
    c = get_color(int(n))
    fs = int(size * 0.45)
    ani = 'floatBall' if animated else ''
    return f'<span class="{ani}" style="display:inline-flex;width:{size}px;height:{size}px;border-radius:50%;background:{c};color:white;font-weight:700;font-size:{fs}px;align-items:center;justify-content:center;margin:2px;box-shadow:0 2px 4px rgba(0,0,0,.15);">{n}</span>'

# ========== 启动 ==========
if __name__ == "__main__":
    print("[启动] 正在初始化...")
    preload_all_data()
        # 预热完成后创建标记文件
    with open("/tmp/ready", "w") as f:
        f.write("ok")
    print("[预热] 完成！")
    
    # --- 新增：启动文件变动监控 ---
    observer = start_file_watcher()
    # ------------------------------
    
    refresh_thread = threading.Thread(target=background_refresh, daemon=True)
    refresh_thread.start()
    print("[启动] 后台刷新线程已启动（每5秒刷新）")

    collector_thread = threading.Thread(target=collector_main, daemon=True)
    collector_thread.start()
    print("[采集] 后台采集线程已启动")     
    
    
    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True
    
    server = ThreadedHTTPServer(('0.0.0.0', PORT), Handler)
    print(f"[网页] 已启动 http://0.0.0.0:{PORT}")
    print(f"[提示] 倒计时每秒更新 | 数据文件变动时自动刷新")
    print(f"[玩法] {', '.join([GAME_DISPLAY_NAMES.get(g, g) for g in GAMES])}")
    print(f"[规则] 6秒尾数80 | 9秒尾数60 | 15秒尾数40 | 30秒尾数20 | 1分钟尾数00")
    server.serve_forever()
