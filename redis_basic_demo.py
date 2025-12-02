"""
Week 12 Redis 快取與資料結構示範（獨立於 Django 專案，便於在課堂 Demo）。

執行方式：
    export REDIS_URI=redis://127.0.0.1:6379/0  # 未設定時使用預設值
    python redis_basic_demo.py
"""

import os

import redis


def main() -> None:
    uri = os.getenv("REDIS_URI", "redis://127.0.0.1:6379/0")
    client = redis.from_url(uri, decode_responses=True)

    print(f"連線至 Redis: {uri}")

    # String
    print("\n[String] set / get / incr / delete")
    client.set("demo:counter", 1)
    print("counter =", client.get("demo:counter"))
    client.incr("demo:counter")
    print("counter after incr =", client.get("demo:counter"))
    client.delete("demo:counter")
    print("counter after delete =", client.get("demo:counter"))

    # Hash
    print("\n[Hash] hset / hgetall / hdel")
    client.hset("demo:user:1", mapping={"name": "Alice", "role": "admin"})
    print("user hash =", client.hgetall("demo:user:1"))
    client.hdel("demo:user:1", "role")
    print("user hash after hdel =", client.hgetall("demo:user:1"))

    # List
    print("\n[List] lpush / lrange / rpop")
    client.delete("demo:queue")
    client.lpush("demo:queue", "task-1", "task-2", "task-3")
    print("queue =", client.lrange("demo:queue", 0, -1))
    print("pop =", client.rpop("demo:queue"))
    print("queue after pop =", client.lrange("demo:queue", 0, -1))


if __name__ == "__main__":
    main()
