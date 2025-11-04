#!/usr/bin/env python
"""
重設 superuser 的腳本
使用方式：python reset_superuser.py
"""
import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def reset_superuser():
    username = input("請輸入新的 superuser 用戶名（預設：admin）：").strip() or "admin"
    email = input("請輸入 email（選填）：").strip() or f"{username}@example.com"
    password = input("請輸入密碼：").strip()
    
    if not password:
        print("錯誤：密碼不能為空")
        return
    
    # 刪除現有的同名用戶（如果存在）
    User.objects.filter(username=username).delete()
    
    # 創建新的 superuser
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    
    print(f"\n✅ Superuser 已創建成功！")
    print(f"   用戶名：{user.username}")
    print(f"   Email：{user.email}")
    print(f"   是否為 superuser：{user.is_superuser}")
    print(f"   是否為 staff：{user.is_staff}")

if __name__ == "__main__":
    try:
        reset_superuser()
    except KeyboardInterrupt:
        print("\n\n已取消操作")
    except Exception as e:
        print(f"\n❌ 錯誤：{e}")

