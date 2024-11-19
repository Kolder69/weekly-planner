import sqlite3


con = sqlite3.connect('UsersInfo.db')
with con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT,
            UserLogin VARCHAR(50) PRIMARY KEY,   -- Логин пользователя, уникальный
            UserPassword TEXT,                  -- Пароль пользователя (захешированный)
            UserName VARCHAR(100),              -- Имя пользователя
            WeekDays TEXT                        -- Ключи пользователя к дням
        );
    """)
