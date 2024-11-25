import sqlite3


con = sqlite3.connect('UsersInfo.db')
with con:
    # Таблица пользователей
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- Уникальный идентификатор пользователя
            UserLogin VARCHAR(50) UNIQUE,        -- Логин пользователя, уникальный
            UserPassword TEXT,                   -- Пароль пользователя (захешированный)
            UserName VARCHAR(100),               -- Имя пользователя
            WeekDays TEXT                        -- Ключи пользователя к дням
        );
    """)

    # Таблица дней и событий
    con.execute("""
        CREATE TABLE IF NOT EXISTS days (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- Уникальный идентификатор дня
            DayDate DATE,                         -- Дата, относящаяся к этому дню
            UserLogin VARCHAR(50),                -- Логин пользователя, которому принадлежит день
            Events TEXT DEFAULT '',               -- События, связанные с этим днём
            FOREIGN KEY (UserLogin) REFERENCES users(UserLogin) -- Связь с таблицей пользователей
        );
    """)