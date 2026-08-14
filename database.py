import sqlite3

import os
import sqlite3

# Автоматически находим точную папку, где лежит этот файл проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Склеиваем путь, чтобы база всегда лежала строго в корне проекта
DB_NAME = os.path.join(BASE_DIR, "afisha_database.db")

print(f"Физический путь к базе данных: {DB_NAME}")


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

    # 2. Создаем таблицу для СОБЫТИЙ
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS events (
                                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                         title TEXT NOT NULL,
                                                         date_info TEXT,
                                                         category TEXT,
                                                         source_url TEXT,
                                                         iso_date TEXT, -- <- ДОБАВЛЯЕМ ЭТО ПОЛЕ ДЛЯ СОРТИРОВКИ ПО КАЛЕНДАРЮ
                                                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                         UNIQUE(title, date_info)
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
        ("Афиша Калининград", "https://afisha.ru/kaliningrad/", "Концерты"),
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

# Этот блок должен запускать СОЗДАНИЕ базы данных, а не её очистку!
if __name__ == "__main__":
    init_db()               # 1. Создает таблицы sources и events с новой колонкой iso_date
    add_initial_sources()   # 2. Загружает в базу наши 7 стартовых сайтов-источников


    # 1. Тот самый полный список мусорных фраз, переведенный в нижний регистр
    garbage_phrases = [
        "получить паспорт туриста", "чем заняться осенью", "чем заняться зимой",
        "чем заняться весной", "чем заняться летом", "о калининградской области",
        "документы для путешествия", "как добраться", "экстренные службы",
        "отправить открытку", "карты и брошюры", "что привезти из калининграда",
        "камеры хранения", "цели и задачи", "гостевая книга", "туризм для профессионалов",
        "бренд калининградской области", "туристский кластер", "туристические фирмы",
        "детский туризм", "гиды и экскурсоводы", "новости туриндустрии", "конференц-залы",
        "обучение экскурсоводов", "инфоцентры в регионе", "инфоцентры в россии",
        "аттестация экскурсоводов и гидов-переводчиков", "добавить свою организацию на сайт",
        "доступный туризм", "туристический портал калининградской области", "афиша",
        "индивидуальные экскурсии с аттестованными гидами", "выдадим карты и путеводители бесплатно!",
        "подскажем самые интересные мероприятия", "составим маршрут для самостоятельного путешествия",
        "подберём туры и экскурсии", "сотрудничаем с объектами туризма", "серебряное ожерелье",
        "афиша мероприятий", "компас балтийской кухни", "о путешествии в ко", "туристический центр",
        "концерты, выставки, фестивали в рамках празднования 80-летия калининградской области",
        "8 (800) 200-55-39", "площадь победы, 1", "ул. октябрьская, 2/3",
        "+7 (4012) 555-200", "info@visit-kaliningrad.ru", "тиц ко",
        "правил посещения игорного заведения", "silver / серебро", "как получить карту",
        "выдается при достижении 5 000 бонусных баллов", "статус gold / золото",
        "выдается при достижении 40 000 бонусных баллов", "platinum / платина",
        "подробнее о программе лояльности", "только по приглашению и наличии от 200 000 бонусных баллов в месяц",
        "пароль", "зарегистрироваться", "вход", "регистрация", "логин", "забыли свой пароль?",
        "карта", "политика", "персональные данные", "конфиденциальность", "согласие",
        "электронная виза", "контакты", "о нас", "о компании", "оферта", "правила",
        "соглашение об обработке персональных данных", "разработка сайта", "продвижение сайта",
        "ответственная игра", "регламенты акций", "политикой обработки персональных данных"
    ]

    print("⏳ Запускаем глубокую Python-очистку базы данных...")

    conn = sqlite3.connect("afisha_database.db")
    cursor = conn.cursor()

    # Извлекаем вообще все события, которые сейчас есть в базе
    cursor.execute("SELECT id, title FROM events")
    all_events = cursor.fetchall()

    deleted_count = 0

    # Перебираем каждое событие в базе
    for event_id, title in all_events:
        title_lower = title.lower().strip()

        # Проверяем, есть ли мусорная фраза внутри названия
        should_delete = False
        for trash in garbage_phrases:
            if trash in title_lower:
                should_delete = True
                break

        # Если нашли совпадение или текст слишком короткий — удаляем строку из базы
        if should_delete or len(title_lower) < 10:
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            deleted_count += 1

    conn.commit()
    conn.close()

    print(f"🧹 Успех! Python распознал русский текст и удалил {deleted_count} мусорных строк.")

