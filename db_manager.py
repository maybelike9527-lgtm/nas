import sqlite3

DB_PATH = 'nas_bot.db'

def init_db():
    """初始化支援分開儲存縣市鄉鎮的資料表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_locations (
            chat_id TEXT PRIMARY KEY,
            city TEXT,
            town TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_user_location(chat_id, city, town):
    conn = sqlite3.connect('nas_bot.db')
    cursor = conn.cursor()
    # 使用 INSERT OR REPLACE 搭配 PRIMARY KEY (chat_id) 達成覆蓋效果
    cursor.execute('''
        INSERT OR REPLACE INTO user_locations (chat_id, city, town, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (str(chat_id), city, town))
    conn.commit()
    conn.close()

def get_user_location(chat_id):
    """獲取分開的地區資料"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT city, town FROM user_locations WHERE chat_id = ?', (str(chat_id),))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None)