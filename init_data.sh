#!/bin/bash
# 資料庫初始化腳本 - 在 Zeabur 終端機執行一次即可

echo "=== Motry 資料初始化 ==="

# 1. 執行遷移
echo "[1/3] 執行資料庫遷移..."
python manage.py migrate --noinput

# 2. 載入車輛資料
echo "[2/3] 載入車輛 fixture..."
python manage.py loaddata vehicles.json

# 3. 載入標籤資料（如果有的話）
echo "[3/3] 載入標籤..."
python manage.py shell -c "
from apps.motry.models import Tag
tags = ['心得分享', '開箱', '改裝', '維修', '比較', '問題討論']
for name in tags:
    Tag.objects.get_or_create(name=name)
print(f'標籤數量: {Tag.objects.count()}')
"

echo "=== 初始化完成 ==="
echo "車輛數量: $(python manage.py shell -c 'from apps.motry.models import Vehicle; print(Vehicle.objects.count())')"
