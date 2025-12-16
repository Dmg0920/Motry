"""
設定模組的選擇改由環境變數 ``DJANGO_SETTINGS_MODULE`` 控制。
預設值在 ``manage.py`` / ``asgi.py`` / ``wsgi.py`` 中設定，
避免這裡強制載入特定環境的設定。
"""
