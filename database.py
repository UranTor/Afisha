import sqlite3

DB_NAME = "afisha_database.db"

def init_db():
    """
    Эта функция создает файл базы данных и нужные таблицы внутри,
    если их еще не существует на компьютере.
    """
    # Подключаемся к файлу базы данных. Если файла нет, Python создаст его сам.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Создаем таблицу для ИСТОЧНИКОВ (сайтов, групп VK)
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS sources (
                                                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                          name TEXT NOT NULL,
                                                          url TEXT UNIQUE NOT NULL,
                                                          category TEXT NOT NULL,
                                                          is_active INTEGER DEFAULT 1
                   )
                   ''')

    # 2. Создаем таблицу для СoБЫТИЙ (сюда парсеры будут складывать афишу)
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS events (
                                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                         title TEXT NOT NULL,
                                                         date_info TEXT,
                                                         category TEXT,
                                                         source_url TEXT,
                                                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                         UNIQUE(title, date_info) -- Защита от дубликатов (чтобы не сохранять одно и то же событие дважды)
                       )
                   ''')

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()
    print("База данных и таблицы успешно инициализированы!")

def add_initial_sources():
    """
    Эта функция автоматически заполнит таблицу источников вашими ссылками,
    чтобы нам не пришлось вбивать их вручную на старте.
    """
    sources = [
        ("GoKaliningrad", "https://gokaliningrad.com", "Общественное мероприятие"),
        ("Клопс Афиша", "https://klops.ru", "Концерты и праздники"),
        ("Яндекс Афиша Калининград", "https://afisha.ru", "Концерты"),
        ("Афиша 80 лет области", "https://visit-kaliningrad.ru", "Общественные мероприятия"),
        ("Казино Собрание", "https://sobranie-casino.com", "Дискотеки и праздники"),
        ("Казино Шамбала", "https://shambala-games.com", "Дискотеки и праздники"),
        ("Мотодвиж39 (VK)", "https://vk.com", "Мото тусовки")
    ]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for name, url, category in sources:
        try:
            # INSERT OR IGNORE означает: если ссылка уже есть в базе, пропустить её и не ломать программу
            cursor.execute(
                "INSERT OR IGNORE INTO sources (name, url, category) VALUES (?, ?, ?)",
                (name, url, category)
            )
        except Exception as e:
            print(f"Ошибка добавления источника {name}: {e}")

    conn.commit()
    conn.close()
    print("Стартовые источники успешно загружены в базу данных!")

# Этот блок запустится, только если мы включим этот файл напрямую
if __name__ == "__main__":
    init_db()
    add_initial_sources()
