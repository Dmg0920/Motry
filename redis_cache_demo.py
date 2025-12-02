"""
Week 12 Redis 快取示範：模擬昂貴計算並快取結果（不需載入 Django）。

執行方式：
    export REDIS_URI=redis://127.0.0.1:6379/0  # 未設定時使用預設值
    python redis_cache_demo.py
"""

import os
import time

import redis


CACHE_KEY = "demo:slow_computation"
CACHE_TTL = 30  # 秒


def slow_computation() -> str:
    """模擬需要數秒的查詢或計算。"""
    time.sleep(2.5)
    return f"result-at-{time.time():.0f}"


def get_or_compute(client: redis.Redis) -> tuple[str, float, bool]:
    """
    若快取存在則直接回傳，否則執行 slow_computation 再寫入快取。
    回傳 (結果, 花費秒數, 是否使用快取)。
    """
    start = time.perf_counter()
    cached = client.get(CACHE_KEY)
    if cached:
        return cached, time.perf_counter() - start, True

    value = slow_computation()
    client.set(CACHE_KEY, value, ex=CACHE_TTL)
    return value, time.perf_counter() - start, False


def main() -> None:
    uri = os.getenv("REDIS_URI", "redis://127.0.0.1:6379/0")
    client = redis.from_url(uri, decode_responses=True)
    print(f"連線至 Redis: {uri}")
    print(f"快取 key: {CACHE_KEY}，TTL: {CACHE_TTL} 秒")

    for i in range(1, 3):
        value, duration, from_cache = get_or_compute(client)
        source = "快取" if from_cache else "重新計算"
        print(f"第 {i} 次取得：{value} | 來源：{source} | 花費 {duration:.3f}s")


if __name__ == "__main__":
    main()
