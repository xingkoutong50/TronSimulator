import os
import csv
import time
import threading
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from collections import defaultdict

PORT = 8081

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
    "6s": 80,
    "9s": 60,
    "15s": 40,
    "30s": 20,
    "1min": 0
}

GAME_SECONDS = {
    "6s": 6,
    "9s": 9,
    "15s": 15,
    "30s": 30,
    "1min": 60
}

GAME_DATA_FILES = {
    "6s": "game_data/6s.csv",
    "9s": "game_data/9s.csv",
    "15s": "game_data/15s.csv",
    "1min": "game_data/1min.csv",
    "30s": "game_data/30s.csv",
}
PREDICT_FILE = "block_prediction_log_v67.csv"

file_lock = threading.Lock()

# ========== 缓存系统 ==========
class DataCache:
    def __init__(self, ttl_seconds=3):
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

cache = DataCache(ttl_seconds=3)

# ========== 获取指定区块时间戳 ==========
def get_block_timestamp(height):
    for retry in range(3):
        try:
            payload = {"num": height}
            r = requests.post(HISTORY_API, json=payload, timeout=10)
            if r.status_code != 200:
                time.sleep(2)
                continue
            data = r.json()
            timestamp = data.get("block_header", {}).get("raw_data", {}).get("timestamp", 0)
            if timestamp:
                return timestamp // 1000
            time.sleep(2)
        except:
            time.sleep(2)
    return None

def get_now_block():
    try:
        r = requests.get(TRON_API, timeout=10)
        data = r.json()
        height = data["block_header"]["raw_data"]["number"]
        block_hash = data["blockID"]
        timestamp = data["block_header"]["raw_data"]["timestamp"] // 1000
        return height, block_hash, timestamp
    except Exception as e:
        print(f"[TRON] 获取最新区块失败: {e}")
        return None, None, None

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
            height, block_hash, timestamp = get_now_block()
            if height is None:
                time.sleep(2)
                continue
            
            target_height, target_hash = find_target_block(height, target_suffix)
            if target_height is None or target_hash is None:
                return None
            
            hash6 = target_hash[-6:]
            last_num = None
            for c in reversed(target_hash):
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
                "hash": target_hash
            }
        except:
            time.sleep(2)
    
    return None

# ========== 加载数据 ==========
def load_realtime_from_csv(game):
    filename = f"history_{game}.csv"
    cache_key = f"realtime_{game}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    data = []
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8", errors="ignore") as f:
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
    
    if len(data) > 500:
        data = data[-500:]
    cache.set(cache_key, data)
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
        data = data[-500:]
    cache.set(cache_key, data)
    return data

def realtime_predict(block_hash, game):
    if not block_hash:
        return {"predict": "-", "model": "-", "predict_block": "-"}
    
    try:
        current_block = int(block_hash)
        suffix = GAME_SUFFIX.get(game, 0)
        next_block = current_block + 1
        while next_block % 20 != suffix:
            next_block += 1
        next_block = str(next_block)
    except:
        next_block = "-"
    
    last_num = None
    for c in reversed(block_hash):
        if c.isdigit():
            last_num = int(c)
            break
    if last_num is None:
        last_num = 0
    
    predict = "单" if last_num % 2 == 1 else "双"
    
    return {
        "predict": predict,
        "model": "Hash 1位",
        "predict_block": next_block,
        "last_num": last_num
    }

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

def preload_all_data():
    print("[预加载] 开始加载所有数据...")
    for g in GAMES:
        load_realtime_from_csv(g)
        load_game_history(g)
    load_predict_logs()
    print("[预加载] 数据加载完成！")

def background_refresh():
    while True:
        time.sleep(3)
        try:
            cache.clear()
            for g in GAMES:
                load_realtime_from_csv(g)
                load_game_history(g)
        except:
            pass

# ========== Handler ==========
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            self.send_api_data()
        else:
            self.send_html_page()
    
    def send_api_data(self):
        """API接口：返回JSON数据"""
        try:
            all_data = {}
            all_stats = {}
            predict_logs = load_predict_logs()
            
            for g in GAMES:
                data = load_realtime_from_csv(g)
                all_data[g] = data
                game_logs = predict_logs.get(g, [])
                all_stats[g] = calc_stat_from_logs(game_logs)
            
            result = {}
            for g in GAMES:
                data = all_data.get(g, [])
                latest = data[-1] if data else {}
                stat = all_stats.get(g, {})
                
                # 计算倒计时 - 用TRON链时间戳
               remaining, total = self.get_countdown_from_block(latest, g)
               remaining = remaining - 23
              if remaining <= 0:
                 remaining = total
              if remaining > total:
                 remaining = total
               
                progress = ((total - remaining) / total * 100) if total > 0 else 0
                
                # 往期开奖（最近30期）
                trend_data = data[-30:] if len(data) >= 30 else data
                trend_list = []
                odd_count = 0
                even_count = 0
                for d in trend_data:
                    if d.get("result") == "单":
                        trend_list.append("单")
                        odd_count += 1
                    else:
                        trend_list.append("双")
                        even_count += 1
                
                pred_result = realtime_predict(latest.get("block", ""), g)
                
                # 历史记录（最近20条）
                history_list = []
                game_predicts = predict_logs.get(g, [])
                predict_dict = {}
                for p in game_predicts:
                    block = p.get("open_block", "")
                    if block:
                        predict_dict[block] = {
                            "predict": p.get("predict", "-"),
                            "result": p.get("result", ""),
                            "time": p.get("time", "")
                        }
                
                recent_history = list(reversed(data[-20:])) if len(data) >= 20 else list(reversed(data))
                for d in recent_history:
                    block = d.get("block", "-")
                    pred_info = predict_dict.get(block, {})
                    history_list.append({
                        "block": block,
                        "hash6": d.get("hash6", "-"),
                        "tail": d.get("tail", "-"),
                        "actual": d.get("result", "-"),
                        "size": d.get("size", "-"),
                        "predict": pred_info.get("predict", "-"),
                        "result_status": pred_info.get("result", ""),
                        "time": pred_info.get("time", "")
                    })
                
                result[g] = {
                    "block": latest.get("block", "-"),
                    "hash6": latest.get("hash6", "-"),
                    "tail": latest.get("tail", "-"),
                    "result": latest.get("result", "-"),
                    "size": latest.get("size", "-"),
                    "countdown": remaining,
                    "total": total,
                    "progress": progress,
                    "trend": trend_list,
                    "odd_count": odd_count,
                    "even_count": even_count,
                    "stats": stat,
                    "predict": pred_result.get("predict", "-"),
                    "predict_block": pred_result.get("predict_block", "-"),
                    "history": history_list
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            print(f"[API错误] {e}")
            self.send_error(500, str(e))
    
    def get_countdown_from_block(self, latest, game):
        """从区块时间戳计算倒计时 - 这是关键"""
        total = GAME_SECONDS.get(game, 30)
        
        block_str = latest.get("block", "")
        if not block_str or block_str == "-":
            # 没有区块数据，用当前时间
            current = (int(time.time()) + 24) % total
            remaining = total - current
            if remaining == 0:
                remaining = total
            return remaining, total
        
        try:
            block_height = int(block_str)
            timestamp = get_block_timestamp(block_height)
            if timestamp:
                # 从区块时间戳计算下一期开奖时间
                # 平台开奖时间是整点秒对齐
                period_start = (timestamp // total) * total
                next_open = period_start + total
                remaining = next_open - int(time.time()) + 24
                # 如果剩余时间小于0，说明已经过了开奖时间，显示下一期
                if remaining <= 0:
                    remaining = total
                if remaining > total:
                    remaining = total
                return remaining, total
        except:
            pass
        
        # 兜底：用当前时间
        current = (int(time.time()) + 24) % total
        remaining = total - current
        if remaining == 0:
            remaining = total
        return remaining, total
    
    def send_html_page(self):
        """发送HTML页面"""
        try:
            html = self.build_full_page()
            
            self.send_response(200)
            self.send_header("Cache-Control", "no-cache")
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            print(f"[错误] {e}")
            self.send_error(500, f"Internal Server Error: {e}")
    
    def build_full_page(self):
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
    <div class="realtime-grid" id="realtimeGrid"><div style="text-align:center;padding:40px;color:#999;">加载中...</div></div>
</div>

<div class="card">
    <div class="section">📊 策略统计</div>
    <div class="stats-grid" id="statsGrid"><div style="text-align:center;padding:40px;color:#999;">加载中...</div></div>
</div>

<div class="card">
    <div class="section">📈 连续走势（√ 命中 / × 错误）</div>
    <div class="streak-grid" id="streakGrid"><div style="text-align:center;padding:40px;color:#999;">加载中...</div></div>
</div>

<div class="card">
    <div class="section">🔴🔵 单双趋势（最近50期）+ 历史验证（最近500期）</div>
    <div class="trend-grid" id="trendGrid"><div style="text-align:center;padding:40px;color:#999;">加载中...</div></div>
</div>

<script>
const GAMES = ["6s", "9s", "15s", "1min", "30s"];
const GAME_DISPLAY = {
    "6s": "6秒哈希",
    "9s": "9秒哈希",
    "15s": "15秒哈希",
    "1min": "1分钟哈希",
    "30s": "30秒哈希"
};
const GAME_SUFFIX = {
    "6s": 80,
    "9s": 60,
    "15s": 40,
    "30s": 20,
    "1min": 0
};
const GAME_TOTAL = {
    "6s": 6,
    "9s": 9,
    "15s": 15,
    "30s": 30,
    "1min": 60
};

// 全局数据缓存
let cachedData = {};

function renderRealtime(data) {
    let html = "";
    for (const g of GAMES) {
        const d = data[g] || {};
        const display_name = GAME_DISPLAY[g] || g;
        const suffix = GAME_SUFFIX[g] || 0;
        const remaining = d.countdown || 0;
        const progress = d.progress || 0;
        const predict = d.predict || "-";
        const predict_color = predict === "单" ? "#ff4444" : "#44bb88";
        const block = d.block || "-";
        const hash6 = d.hash6 || "-";
        const tail = d.tail || "-";
        const result = d.result || "-";
        const size = d.size || "-";
        const predict_block = d.predict_block || "-";
        const odd_count = d.odd_count || 0;
        const even_count = d.even_count || 0;
        
        let trendDots = "";
        const trendData = d.trend || [];
        if (trendData.length > 0) {
            for (const item of trendData) {
                const cls = item === "单" ? "odd" : "even";
                trendDots += `<span class="trend-dot-platform ${cls}">${item}</span>`;
            }
        } else {
            trendDots = '<span style="color:#999;font-size:0.7rem;">暂无数据</span>';
        }
        
        html += `
        <div class="realtime-item" id="card-${g}">
            <div class="realtime-header">
                <span class="play-name">${display_name}</span>
                <span class="countdown-badge">⏱ <span class="countdown-number" id="cd-${g}">${remaining}</span> 秒</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="pg-${g}" style="width:${progress}%;"></div>
            </div>
            <div class="block-display">
                <div class="block-left">
                    <div class="block-label">📌 已开奖 (尾数 ${suffix})</div>
                    <div class="block-number">${block}</div>
                    <div class="block-detail">验证 ${tail}</div>
                </div>
                <div class="block-right">
                    <div class="block-label">🎯 下注</div>
                    <div class="block-number">${predict_block}</div>
                    <div class="block-detail">...${hash6}</div>
                    <div class="block-result" style="color:${predict_color};font-size:1.8rem;font-weight:900;text-shadow:0 0 20px ${predict_color}40;">预测 ${predict}</div>
                </div>
            </div>
            <div class="trend-section">
                <div class="trend-header">
                    <span style="font-size:0.7rem;font-weight:600;color:#555;">📊 往期开奖</span>
                    <span style="font-size:0.7rem;font-weight:600;color:#888;">单 ${odd_count} 双 ${even_count}</span>
                </div>
                <div class="trend-dots">${trendDots}</div>
            </div>
        </div>
        `;
    }
    document.getElementById('realtimeGrid').innerHTML = html;
}

function renderStats(data) {
    let html = "";
    for (const g of GAMES) {
        const d = data[g] || {};
        const stat = d.stats || {};
        const display_name = GAME_DISPLAY[g] || g;
        html += `
        <div class="cardHover stats-item">
            <div class="play-name">${display_name}</div>
            <div>总次数: ${stat.total || 0}</div>
            <div>命中: ${stat.hits || 0} | 错误: ${stat.misses || 0}</div>
            <div style="font-size:1.2rem;font-weight:700;color:#c44545;margin:4px 0;">${stat.hit_rate || 0}%</div>
            <div>最大连中: ${stat.max_win || 0} | 最大连挂: ${stat.max_lose || 0}</div>
            <div class="status">当前: ${stat.current_status || "无"}</div>
        </div>
        `;
    }
    document.getElementById('statsGrid').innerHTML = html;
}

function renderStreak(data) {
    let html = "";
    for (const g of GAMES) {
        const d = data[g] || {};
        const display_name = GAME_DISPLAY[g] || g;
        const history = d.history || [];
        let dots = "";
        const recent = history.slice(0, 30);
        for (const item of recent) {
            if (item.result_status === "命中") {
                dots += '<span class="streak-dot hit">√</span>';
            } else if (item.result_status === "错误") {
                dots += '<span class="streak-dot miss">×</span>';
            } else {
                dots += '<span class="streak-dot" style="background:#f0f0f0;color:#999;">-</span>';
            }
        }
        html += `
        <div class="streak-item">
            <div class="play-name">${display_name}</div>
            <div class="streak-dots">${dots || '<span style="color:#999;font-size:0.7rem;">暂无数据</span>'}</div>
        </div>
        `;
    }
    document.getElementById('streakGrid').innerHTML = html;
}

function renderTrendAndHistory(data) {
    let html = "";
    for (const g of GAMES) {
        const d = data[g] || {};
        const display_name = GAME_DISPLAY[g] || g;
        const history = d.history || [];
        
        let dots = "";
        let odd_count = 0;
        let even_count = 0;
        const trendData = d.trend || [];
        for (const item of trendData) {
            const cls = item === "单" ? "odd" : "even";
            dots += `<span class="trend-dot ${cls}">${item}</span>`;
            if (item === "单") odd_count++;
            else even_count++;
        }
        const total = odd_count + even_count;
        const odd_pct = total > 0 ? Math.round(odd_count/total*100) : 0;
        const even_pct = total > 0 ? Math.round(even_count/total*100) : 0;
        
        let historyRows = "";
        const recentHistory = history.slice(0, 20);
        for (const item of recentHistory) {
            const timeStr = item.time ? item.time.slice(-8) : "-";
            const resultDisplay = item.result_status === "命中" ? '<span style="color:#2e7d32;font-weight:700;">√ 中</span>' :
                                   item.result_status === "错误" ? '<span style="color:#c62828;font-weight:700;">× 挂</span>' :
                                   '<span style="color:#999;">-</span>';
            historyRows += `
            <tr>
                <td style="font-size:.75rem;padding:4px 6px;text-align:center;">${timeStr}</td>
                <td style="font-size:.75rem;padding:4px 6px;text-align:center;font-weight:600;">${item.block || "-"}</td>
                <td style="font-size:.75rem;padding:4px 6px;text-align:center;font-weight:600;color:#1a3a5c;">${item.hash6 || "-"}</td>
                <td style="font-size:.75rem;padding:4px 6px;text-align:center;font-weight:600;color:#1a3a5c;">${item.actual || "-"}</td>
                <td style="font-size:.75rem;padding:4px 6px;text-align:center;font-weight:600;color:#1a3a5c;">${item.size || "-"}</td>
                <td style="font-size:.75rem;padding:4px 6px;text-align:center;font-weight:600;color:#c44545;">${item.predict || "-"}</td>
                <td style="font-size:.75rem;padding:4px 6px;text-align:center;">${resultDisplay}</td>
            </tr>`;
        }
        
        html += `
        <div class="trend-item" style="display:flex;flex-direction:column;background:#fafbfc;border:1px solid #e8ecf1;border-radius:8px;padding:12px;">
            <div class="play-name" style="font-weight:700;font-size:1.2rem;color:#1a3a5c;margin-bottom:6px;text-align:center;">${display_name}</div>
            <div class="trend-dots" style="display:flex;flex-wrap:wrap;gap:3px;justify-content:center;margin:6px 0;">${dots || '<span style="color:#999;font-size:0.7rem;">暂无数据</span>'}</div>
            <div class="trend-count" style="font-size:.8rem;color:#666;text-align:center;margin-bottom:8px;font-weight:600;">单: ${odd_count}次(${odd_pct}%) | 双: ${even_count}次(${even_pct}%)</div>
            <div style="border-top:2px solid #e8ecf1;padding-top:8px;margin-top:4px;">
                <div style="font-size:.8rem;font-weight:700;color:#1a3a5c;margin-bottom:6px;text-align:center;">📋 ${display_name} 历史验证（最近${recentHistory.length}期）</div>
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
                            ${historyRows || '<tr><td colspan="7" style="text-align:center;color:#999;font-size:.75rem;padding:12px;">暂无数据</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        `;
    }
    document.getElementById('trendGrid').innerHTML = html;
}

function fetchData() {
    fetch('/api/data')
        .then(res => res.json())
        .then(data => {
            cachedData = data;
            renderRealtime(data);
            renderStats(data);
            renderStreak(data);
            renderTrendAndHistory(data);
        })
        .catch(err => console.error('获取数据失败:', err));
}

// ===== 倒计时只从后端数据更新，前端不再自己计算 =====
function updateCountdowns() {
    // 直接从 cachedData 里取后端算好的 countdown 显示
    for (const g of GAMES) {
        const d = cachedData[g] || {};
        const remaining = d.countdown || 0;
        const total = GAME_TOTAL[g] || 30;
        const progress = d.progress || 0;
        const el = document.getElementById('cd-' + g);
        const pg = document.getElementById('pg-' + g);
        if (el) el.textContent = remaining;
        if (pg) {
            pg.style.width = progress + '%';
        }
    }
}

// 启动
fetchData();
setInterval(fetchData, 3000);

// 倒计时每秒更新（从后端数据取）
setInterval(updateCountdowns, 1000);
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
    
    refresh_thread = threading.Thread(target=background_refresh, daemon=True)
    refresh_thread.start()
    print("[启动] 后台刷新线程已启动（每3秒刷新）")
    
    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True
    
    server = ThreadedHTTPServer(('0.0.0.0', PORT), Handler)
    print(f"[网页] 已启动 http://0.0.0.0:{PORT}")
    print(f"[提示] 倒计时从后端TRON链时间戳计算 | 每3秒更新数据")
    print(f"[玩法] {', '.join([GAME_DISPLAY_NAMES.get(g, g) for g in GAMES])}")
    print(f"[规则] 6秒尾数80 | 9秒尾数60 | 15秒尾数40 | 30秒尾数20 | 1分钟尾数00")
    server.serve_forever()