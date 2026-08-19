import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "afisha_database.db")


def parse_gokaliningrad():
    """ 1. Оптимизированный парсер GoKaliningrad по трем разделам """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    collected_events = []

    # Словарь целевых разделов с привязкой к точным категориям
    sections = {
        "https://gokaliningrad.com/tour/list": "Экскурсии",
        "https://gokaliningrad.com/museum/list": "Выставки",
        "https://gokaliningrad.com/museumgeo/list": "Музеи"
    }

    print("Парсер GoKaliningrad запущен...")

    # Последовательный обход каждого раздела
    for target_url, category_name in sections.items():
        try:
            response = requests.get(target_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Ошибка загрузки раздела {target_url}: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            titles = soup.find_all('div', class_='v-card__title')

            for title_block in titles:
                event_title = title_block.text.strip()
                parent_card = title_block.find_parent()

                date_text = "Расписание уточняйте на сайте"
                if parent_card:
                    text_block = parent_card.find('div', class_='v-card__text')
                    if text_block:
                        date_text = text_block.get_text(separator=" | ", strip=True)

                # Формирование пакета данных с точной категорией и ссылкой на подраздел
                event_data = {
                    "title": event_title,
                    "date_info": date_text,
                    "category": category_name,
                    "source": target_url
                }
                collected_events.append(event_data)

        except Exception as e:
            print(f"Ошибка при парсинге раздела {target_url}: {e}")

    return collected_events


def parse_casino_sobranie():
    """ 3. Оптимизированный парсер Казино Собрание (раздел Шоу) """
    url = "https://www.sobranie-casino.com/ru/current/show/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    collected_events = []
    print("Парсер Казино Собрание запущен...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Ошибка загрузки Казино Собрание: {response.status_code}")
            return collected_events

        soup = BeautifulSoup(response.text, 'html.parser')

        # Поиск стандартных контейнеров карточек мероприятий
        event_items = soup.find_all('li', class_='events-list__item') or \
                      soup.find_all('a', class_='events-list__item') or \
                      soup.find_all('div', class_='events-item')

        print(f"Найдено сырых блоков афиши: {len(event_items)}")

        for item in event_items:
            title_block = item.find(class_='events-item__title') or \
                          item.find(class_='title') or \
                          item.find('h3')

            date_block = item.find(class_='events-item__date') or \
                         item.find(class_='date') or \
                         item.find(class_='events-item__time')

            if title_block:
                title = title_block.text.strip()
                if not title:
                    continue

                date_text = date_block.text.strip() if date_block else "Дата на сайте казино"
                date_text = " ".join(date_text.split())

                collected_events.append({
                    "title": title,
                    "date_info": date_text,
                    "category": "Дискотеки и праздники",
                    "source": url
                })

        # Аварийный сбор по ссылкам, если стандартные карточки не найдены в HTML
        if not collected_events:
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/event/' in href:
                    title = link.text.strip()
                    if title and len(title) > 5:
                        clean_title = " ".join(title.split())
                        full_url = href if href.startswith('http') else "https://www.sobranie-casino.com" + href
                        collected_events.append({
                            "title": clean_title,
                            "date_info": "Уточняйте на сайте казино",
                            "category": "Дискотеки и праздники",
                            "source": full_url
                        })

        # Внутренняя очистка списка от дубликатов перед возвратом данных
        unique_events = []
        seen_titles = set()
        for ev in collected_events:
            if ev["title"] not in seen_titles:
                seen_titles.add(ev["title"])
                unique_events.append(ev)
        return unique_events

    except Exception as e:
        print(f"Ошибка при парсинге Казино Собрание: {e}")

    return collected_events


def parse_casino_shambala():
    """ 4. Оптимизированный всеядный парсер Казино Шамбала (Gambling Weekend) """
    url = "https://shambala-games.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    collected_events = []
    print("Парсер Казино Шамбала запущен...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Ошибка загрузки Шамбалы: {response.status_code}")
            return collected_events

        soup = BeautifulSoup(response.text, 'html.parser')

        # Расширяем поиск до заголовков и текстовых параграфов для всеядного захвата
        for block in soup.find_all(['h2', 'h3', 'p']):
            title = block.text.strip()

            # Сужаем диапазон длины: названия шоу на Шамбале обычно укладываются в эти рамки
            if title and 20 < len(title) < 80:
                local_stop = [
                    "главная", "контакты", "оферта", "правила", "казино", "о нас",
                    "игры", "новости", "ресторан", "отель", "турниры", "конфиденциальность",
                    "согласие", "карта", "программа", "лояльность", "суббота", "пятница",
                    "политика", "обработка", "вход", "заведение", "игорного", "внимание"
                ]
                if any(word in title.lower() for word in local_stop):
                    continue

                clean_title = " ".join(title.split())

                collected_events.append({
                    "title": clean_title,
                    "date_info": "Выходные дни / Уточняйте на сайте казино",
                    "category": "Дискотеки и праздники",
                    "source": url
                })

        # Финальное удаление внутренних дубликатов строк
        unique_events = []
        titles_seen = set()
        for ev in collected_events:
            if ev["title"] not in titles_seen:
                titles_seen.add(ev["title"])
                unique_events.append(ev)

        return unique_events

    except Exception as e:
        print(f"Ошибка при парсинге Казино Шамбала: {e}")

    return collected_events





def parse_afisha_80let():
    """ 6. Высокоточный парсер ТИЦ Калининград (Разделы Афиша и Календарь) """
    import datetime
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    collected_events = []
    print("Парсер Афиши 80 лет области запущен...")

    # Вычисляем текущую дату для правильного запроса к календарю
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # Жестко прописываем правильные адреса страниц прямо внутри функции
    sections = {
        "https://visit-kaliningrad.ru": "Общественные мероприятия",
        f"https://visit-kaliningrad.ru{today_str}": "Календарь событий"
    }

    for target_url, category_name in sections.items():
        try:
            response = requests.get(target_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Ошибка загрузки раздела {category_name}: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # --- ВЕТКА 1: ОБРАБОТКА ХРОНОЛОГИЧЕСКОГО КАЛЕНДАРЯ ---
            if "calendar" in target_url:
                # На этой странице данные идут сплошным текстом. Собираем параграфы или дивы.
                # Мы ищем ключевые маркеры структуры, которую вы описали
                text_blocks = soup.find_all(['div', 'p', 'span'])

                current_date = "Дата уточняется"
                for block in text_blocks:
                    text = block.get_text(strip=True)

                    # Ловим маркер даты
                    if text.lower() == "дата" or text.lower().startswith("дата:"):
                        # Обычно сама дата идет в следующем элементе, либо в этом же
                        continue

                    # Ловим маркер мероприятия
                    if "мероприятие" in text.lower():
                        # Вытаскиваем чистое название события из соседнего блока или очищаем строку
                        event_title = text.replace("мероприятие", "").replace("Мероприятие", "").strip(" :")

                        if event_title and len(event_title) > 10:
                            collected_events.append({
                                "title": "Календарь: " + " ".join(event_title.split()),
                                "date_info": "Смотрите в календаре ТИЦ",
                                "category": "Общественные мероприятия",
                                "source": "https://visit-kaliningrad.ru"
                            })

            # --- ВЕТКА 2: ОБРАБОТКА СТАНДАРТНОЙ АФИШИ ССЫЛОК ---
            else:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    title = link.text.strip()

                    if "/events/" in href and href != "/events/":
                        if title and len(title) > 12:
                            local_stop = ["карта", "маршруты", "о нас", "контакты", "назад"]
                            if any(word in title.lower() for word in local_stop):
                                continue

                            clean_title = " ".join(title.split())
                            full_url = href if href.startswith('http') else "https://visit-kaliningrad.ru" + href

                            collected_events.append({
                                "title": clean_title,
                                "date_info": "Смотрите на visit-kaliningrad.ru",
                                "category": "Общественные мероприятия",
                                "source": "https://visit-kaliningrad.ru"
                            })

        except Exception as e:
            print(f"Ошибка при парсинге раздела {category_name}: {e}")

    # Удаление внутренних дубликатов строк
    unique_events = []
    titles_seen = set()
    for ev in collected_events:
        if ev["title"] not in titles_seen:
            titles_seen.add(ev["title"])
            unique_events.append(ev)

    return unique_events



















def parse_afisha_kaliningrad():
    """ 7. Парсер Афиши Калининград (afisha.ru) """
    url = "https://afisha.ru/kaliningrad/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    collected_events = []

    print("Парсер Афиши Калининград запущен...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Поиск всех ссылок на странице для извлечения названий
            for link in soup.find_all('a', href=True):
                title = link.text.strip()
                href = link['href']

                # Фильтрация по длине текста для отсечения коротких пунктов меню
                if title and len(title) > 12:
                    # Исключение служебных переходов
                    if any(word in title.lower() for word in ["купить", "билеты", "выбрать", "акции", "скидки", "кабинет"]):
                        continue

                    clean_title = " ".join(title.split())
                    full_url = href if href.startswith('http') else "https://afisha.ru/kaliningrad/" + href

                    collected_events.append({
                        "title": clean_title,
                        "date_info": "Уточняйте на Afisha.ru",
                        "category": "Концерты",
                        "source": url
                    })
    except Exception as e:
        print(f"Ошибка Афиши Калининград: {e}")
    return collected_events


def parse_yandex_kaliningrad():
    """ 8. Парсер Яндекс Калининград (afisha.yandex.ru) """
    url = "https://afisha.yandex.ru/kaliningrad"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    collected_events = []

    print("Парсер Яндекс Калининград запущен...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Сбор текстовых ссылок на мероприятия
            for link in soup.find_all('a', href=True):
                title = link.text.strip()
                href = link['href']

                if title and len(title) > 12:
                    # Исключение служебных элементов интерфейса Яндекса
                    if any(word in title.lower() for word in ["купить", "билеты", "выбрать", "акции", "вход", "кабинет"]):
                        continue

                    clean_title = " ".join(title.split())
                    full_url = href if href.startswith('http') else "https://afisha.yandex.ru" + href

                    collected_events.append({
                        "title": clean_title,
                        "date_info": "Уточняйте на Яндекс Афише",
                        "category": "Концерты",
                        "source": url
                    })
    except Exception as e:
        print(f"Ошибка Яндекс Калининград: {e}")
    return collected_events


def parse_klops_afisha():
    """ 5. Высокотехнологичный автономный парсер Клопс Афиши на движке Selenium """
    collected_events = []
    print("Парсер Клопс Афиши запущен...")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Актуальный фоновый режим для Chrome
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Защита от блокировок по сети
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Попытка найти стандартный путь к Google Chrome на Windows, если Selenium его теряет
    possible_chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    for path in possible_chrome_paths:
        if os.path.exists(path):
            chrome_options.binary_location = path
            break

    sections = {
        "https://klops.ru": "Концерты",
        "https://klops.ru": "Театр",
        "https://klops.ru": "Выставки"
    }

    driver = None
    try:
        # Инициализируем браузер. Selenium 4+ сам свяжется с системным Chrome
        # через установленные бинарные файлы без скачивания внешних драйверов.
        driver = webdriver.Chrome(options=chrome_options)

        for target_url, category_name in sections.items():
            print(f"Браузер загружает раздел Клопс: {category_name}...")
            driver.get(target_url)

            # Ожидание 4 секунды для отработки тяжелых JS-скриптов Клопса
            time.sleep(4)

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            for link in soup.find_all('a', href=True):
                href = link['href']

                if '/afisha/event/' in href or '/event/' in href:
                    title = link.text.strip()

                    if title and len(title) > 12:
                        if any(word in title.lower() for word in ["купить", "билет", "подробнее"]):
                            continue

                        clean_title = " ".join(title.split())
                        full_url = href if href.startswith('http') else "https://klops.ru" + href

                        collected_events.append({
                            "title": clean_title,
                            "date_info": "Уточняйте расписание на Klops.ru",
                            "category": category_name,
                            "source": target_url
                        })

    except Exception as e:
        print(f"Критическая ошибка Selenium при парсинге Клопса: {e}")
    finally:
        if driver:
            driver.quit()

    unique_events = []
    titles_seen = set()
    for ev in collected_events:
        if ev["title"] not in titles_seen:
            titles_seen.add(ev["title"])
            unique_events.append(ev)

    return unique_events



def save_events_to_db(events_list):
    """
    Функция записывает события в базу данных SQLite,
    автоматически фильтруя системный мусор и технические ссылки.
    """
    conn = sqlite3.connect("afisha_database.db")
    cursor = conn.cursor()

    # Оптимизированный список стоп-слов (удалены дубликаты и поглощаемые строки)
    stop_words = [
        # --- Системные и технические термины ---
        "пароль", "зарегистрироваться", "вход", "регистрация", "логин",
        "карта", "политика", "персональные данные", "конфиденциальность",
        "электронная виза", "контакты", "о нас", "о компании", "оферта",
        "правила", "новости", "назад", "главная", "показать все", "купить билет",
        "все концерты", "подробнее", "кабинет", "профиль", "согласие",
        "забыли свой пароль?", "соглашение об обработке персональных данных",
        "разработка сайта:", "продвижение сайта:", "ответственная игра",
        "регламенты акций",

        # --- Навигация и инфо-блоки visit-kaliningrad ---
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
        "компас балтийской кухни", "о путешествии в ко", "туристический центр",
        "концерты, выставки, фестивали в рамках празднования 80-летия калининградской области",

        # --- Адреса, контакты и телефоны ---
        "8 (800) 200-55-39", "площадь победы, 1", "ул. октябрьская, 2/3",
        "+7 (4012) 555-200", "info@visit-kaliningrad.ru", "тиц ко",

        # --- Элементы программы лояльности казино (Шамбала / Собрание) ---
        "правил посещения игорного заведения", "silver / серебро", "как получить карту",
        "выдается при достижении 5 000 бонусных баллов", "статус gold / золото",
        "выдается при достижении 40 000 бонусных баллов", "platinum / платина",
        "подробнее о программе лояльности", "только по приглашению и наличии от 200 000 бонусных баллов в месяц"
    ]

    saved_count = 0

    for event in events_list:
        title = event["title"]

        # 1. Проверка на стоп-слова
        if any(word in title.lower() for word in stop_words):
            continue

        # 2. Проверка на длину строки
        if len(title.strip()) < 10:
            continue

        try:
            # Запись данных по 4 стандартным колонкам текущей схемы БД
            cursor.execute('''
                           INSERT OR IGNORE INTO events (title, date_info, category, source_url)
                VALUES (?, ?, ?, ?)
                           ''', (title, event["date_info"], event["category"], event["source"]))

            if cursor.rowcount > 0:
                saved_count += 1
                conn.commit()  # Фиксация строки сразу для защиты от блокировок
        except Exception as e:
            print(f"Ошибка записи события в БД: {e}")

    conn.close()
    print(f"Фильтрация завершена. В базу данных добавлено чистых событий: {saved_count}")


def run_all_parsers():
    """
    Главный диспетчер. Он опрашивает базу данных, находит активные источники
    и автоматически распределяет, какого робота запустить для каждого сайта.
    """
    print("\n=== ЗАПУСК ГЛОБАЛЬНОГО СБОРЩИКА АФИШИ ===")

    # Привязка к абсолютному имени файла для исключения ошибок поиска таблиц
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, url FROM sources WHERE is_active = 1")
    active_sources = cursor.fetchall()
    conn.close()

    print(f"В базе данных найдено активных источников для проверки: {len(active_sources)}")
    print("=" * 40)

    for name, url in active_sources:
        print(f"\nПроверяем источник: {name} ({url})")
        results = []

        if "gokaliningrad.com" in url:
            results = parse_gokaliningrad()
        elif "afisha.ru" in url:
            results = parse_afisha_kaliningrad()
        elif "yandex.ru" in url:
            results = parse_yandex_kaliningrad()
        elif "sobranie-casino.com" in url:
            results = parse_casino_sobranie()
        elif "shambala-games.com" in url:
            results = parse_casino_shambala()
        elif "klops.ru" in url:
            results = parse_klops_afisha()
        elif "visit-kaliningrad.ru" in url:
            results = parse_afisha_80let()
        else:
            print(f"⚠️ Для сайта {name} еще не написан точный парсер. Пропускаем.")
            continue

        print(f"-> Собрано событий: {len(results)}")
        if results:
            save_events_to_db(results)


if __name__ == "__main__":
    run_all_parsers()
