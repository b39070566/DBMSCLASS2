import sqlite3
import os
from dotenv import load_dotenv

# 載入 .env 變數
load_dotenv()

# 從 .env 讀取資料庫路徑，若沒設定則預設使用 db2025class
DB_PATH = os.getenv('db2025class', 'db2025class')

# 連線到 SQLite 資料庫（若檔案不存在會自動建立）
connection = sqlite3.connect(DB_PATH, check_same_thread=False)

# 建立 cursor
cursor = connection.cursor()

print(f"已成功連線到 SQLite 資料庫：{DB_PATH}")