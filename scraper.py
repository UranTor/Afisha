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
    """ 6. Стабильный парсер ТИЦ Калининград (Раздел Афиша + Карточка-заглушка Календаря) """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    collected_events = []
    print("Парсер Афиши 80 лет области запущен...")

    # --- ЧАСТЬ 1: ГЕНЕРАЦИЯ УНИВЕРСАЛЬНОЙ КАРТОЧКИ-ЗАГЛУШКИ ДЛЯ КАЛЕНДАРЯ ---
    calendar_url = "https://visit-kaliningrad.ru"
    collected_events.append({
        "title": "📅 Сводный календарь крупных городских и туристических событий Калининградской области",
        "date_info": "Актуальное расписание на весь год (обновляется ТИЦ)",
        "category": "Общественные мероприятия",
        "source": calendar_url
    })

    # --- ЧАСТЬ 2: СБОР ТЕКУЩИХ СОБЫТИЙ ИЗ СТАНДАРТНОГО РАЗДЕЛА АФИШИ ---
    events_url = "https://visit-kaliningrad.ru"
    try:
        response = requests.get(events_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Сканируем ссылки, ведущие на конкретные карточки мероприятий
            for link in soup.find_all('a', href=True):
                href = link['href']
                title = link.text.strip()

                # Отбираем только детальные страницы событий, отсекаем ссылки на разделы меню
                if "/events/" in href and href != "/events/":
                    if title and len(title) > 12:
                        # Локальный черный список для защиты от системных надписей
                        local_stop = ["карта", "маршруты", "о нас", "контакты", "назад", "подробнее", "купить билет"]
                        if any(word in title.lower() for word in local_stop):
                            continue

                        clean_title = " ".join(title.split())
                        full_url = href if href.startswith('http') else "https://visit-kaliningrad.ru" + href

                        collected_events.append({
                            "title": clean_title,
                            "date_info": "Смотрите подробности на visit-kaliningrad.ru",
                            "category": "Общественные мероприятия",
                            "source": full_url
                        })
        else:
            print(f"Предупреждение: Раздел афиши ТИЦ вернул статус {response.status_code}")

    except Exception as e:
        print(f"Ошибка при парсинге раздела стандартной афиши ТИЦ: {e}")

    # Удаление внутренних дубликатов строк перед отправкой в базу данных
    unique_events = []
    titles_seen = set()
    for ev in collected_events:
        if ev["title"] not in titles_seen:
            titles_seen.add(ev["title"])
            unique_events.append(ev)

    return unique_events


def parse_afisha_kaliningrad():
    """ 7. Оптимизированный многостраничный парсер Афиши Калининград (afisha.ru) """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    collected_events = []

    # Словарь целевых адресов разделов с жесткой привязкой к смысловым категориям
    sections = {
        "https://www.afisha.ru/kaliningrad/events/exhibitions/concerts/excursions/": "Экскурсии",
        "https://www.afisha.ru/kaliningrad/party/": "Дискотеки и праздники",
        "https://www.afisha.ru/kaliningrad/schedule_exhibition/": "Выставки",
        "https://www.afisha.ru/kaliningrad/schedule_concert/": "Концерты",
        "https://www.afisha.ru/kaliningrad/festivals/": "Дискотеки и праздники" # Категория под Фестивали из вашей структуры select формы
    }

    print("Парсер Афиши Калининград запущен...")

    # Последовательный обход всех 5 разделов
    for target_url, category_name in sections.items():
        try:
            response = requests.get(target_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Ошибка загрузки подраздела {category_name}: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            for link in soup.find_all('a', href=True):
                title = link.text.strip()
                href = link['href']

                # Фильтрация по длине строки для удаления элементов интерфейса
                if title and len(title) > 12:
                    # Черный список для отсечения служебной навигации afisha.ru
                    if any(word in title.lower() for word in ["купить", "билеты", "выбрать", "акции", "скидки", "кабинет", "подборки", " daily "]):
                        continue

                    clean_title = " ".join(title.split())
                    full_url = href if href.startswith('http') else "https://www.afisha.ru" + href

                    collected_events.append({
                        "title": clean_title,
                        "date_info": "Уточняйте расписание на Afisha.ru",
                        "category": category_name,
                        "source": target_url
                    })
        except Exception as e:
            print(f"Ошибка при парсинге подраздела {category_name}: {e}")

    # КРИТИЧЕСКИ ВАЖНО: Удаление дубликатов заголовков перед передачей в БД
    unique_events = []
    seen_titles = set()
    for ev in collected_events:
        if ev["title"] not in seen_titles:
            seen_titles.add(ev["title"])
            unique_events.append(ev)

    return unique_events


def parse_yandex_kaliningrad():
    """ 8. Оптимизированный многостраничный парсер Яндекс Калининград (afisha.yandex.ru) """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    collected_events = []

    # Словарь 7 целевых адресов Яндекса с привязкой к категориям вашей базы данных
    sections = {
        "https://afisha.yandex.ru/kaliningrad/concert?utm_source=ya&utm_medium=main&utm_campaign=main_services&source=menu&multiFilter=2.concert%2C7.non-children": "Концерты",
        "https://afisha.yandex.ru/kaliningrad/festival?utm_source=ya&utm_medium=main&utm_campaign=main_services&source=menu": "Дискотеки и праздники",
        "https://afisha.yandex.ru/kaliningrad/theatre?utm_source=ya&utm_medium=main&utm_campaign=main_services&source=menu": "Театр",
        "https://afisha.yandex.ru/kaliningrad/standup?utm_source=ya&utm_medium=main&utm_campaign=main_services&source=menu": "Концерты", # Стендап относим к концертам/юмору
        "https://afisha.yandex.ru/kaliningrad/art?utm_source=ya&utm_medium=main&utm_campaign=main_services&source=menu": "Выставки",
        "https://afisha.yandex.ru/kaliningrad/show?utm_source=ya&utm_medium=main&utm_campaign=main_services&source=menu": "Дискотеки и праздники", # Шоу относим к праздникам
        "https://afisha.yandex.ru/kaliningrad/excursions?utm_source=ya&utm_medium=main&utm_campaign=main_services&source=menu": "Экскурсии"
    }

    print("Парсер Яндекс Калининград запущен...")

    # Последовательный обход всех 7 разделов
    for target_url, category_name in sections.items():
        try:
            response = requests.get(target_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Ошибка загрузки раздела Яндекса {category_name}: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # СТРОГИЙ ТОЧЕЧНЫЙ ФИЛЬТР: Карточки событий на Яндекс Афише всегда используют тег h2 для названий.
            # Это полностью исключает попадание списка городов, меню навигации и подвала сайта.
            for block in soup.find_all('h2'):
                title = block.text.strip()

                # Отсекаем пустые блоки и слишком короткие технические строки
                if title and len(title) > 5:
                    # Локальный черный список для исключения заголовков блоков рекомендаций
                    if any(word in title.lower() for word in ["подборки", "скачайте приложение", "это вы?"]):
                        continue

                    clean_title = " ".join(title.split())

                    collected_events.append({
                        "title": clean_title,
                        "date_info": "Уточняйте расписание на Яндекс Афише",
                        "category": category_name,
                        "source": target_url
                    })
        except Exception as e:
            print(f"Ошибка при парсинге раздела Яндекса {category_name}: {e}")

    # УДАЛЕНИЕ ДУБЛИКАТОВ: Фильтруем повторы заголовков перед передачей в диспетчер
    unique_events = []
    seen_titles = set()
    for ev in collected_events:
        if ev["title"] not in seen_titles:
            seen_titles.add(ev["title"])
            unique_events.append(ev)

    return unique_events


def parse_klops_afisha():
    """ 5. Высокотехнологичный автономный парсер Клопс Афиши на движке Selenium """
    collected_events = []
    print("Парсер Клопс Афиши запущен...")

    chrome_options = Options()
    # АКТИВАЦИЯ ФОНОВОГО РЕЖИМА: Теперь окно браузера открываться на экране НЕ БУДЕТ
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Защита от блокировок
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    possible_chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    for path in possible_chrome_paths:
        if os.path.exists(path):
            chrome_options.binary_location = path
            break

    # СТРОГО ВАШИ ОРИГИНАЛЬНЫЕ АДРЕСА СТРАНИЦ ПОИСКА КЛОПСА:
    sections = {
        "https://klops.ru/afisha/search?search=&category=kontserty&period=plus_year": "Концерты",
        "https://klops.ru/afisha/search?search=&category=teatr&period=plus_year": "Театр",
        "https://klops.ru/afisha/search?search=&category=vystavki&period=plus_year": "Выставки"
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)

        for target_url, category_name in sections.items():
            print(f"Браузер физически открывает раздел Клопс: {category_name}...")
            driver.get(target_url)

            # Пауза 5 секунд для полной отрисовки карточек скриптами JavaScript
            time.sleep(5)

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Точечный сбор названий мероприятий по тегам h4 из текстового слепка
            for block in soup.find_all('h4'):
                title = block.text.strip()

                if title and len(title) > 8:
                    if any(word in title.lower() for word in ["афиша клопс", "билеты на", "купить билет"]):
                        continue

                    clean_title = " ".join(title.split())

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
    Функция записывает чистые события в базу данных SQLite,
    применяя двухуровневую фильтрацию (RegEx + расширенные стоп-слова).
    Запись идет строго по 4 стандартным колонкам.
    """
    import re
    import sqlite3

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ОБЪЕДИНЕННЫЙ И РАСШИРЕННЫЙ СПИСОК СТОП-СЛОВ ДЛЯ ПОЛНОЙ ЗАЧИСТКИ
    stop_words = [
        # --- Системные и b2b-термины (Афиша / Яндекс / Шамбала) ---
        "пароль", "зарегистрироваться", "вход", "регистрация", "логин", "забыли свой пароль?",
        "карта", "политика", "персональные данные", "конфиденциальность", "согласие",
        "электронная виза", "контакты", "о нас", "о компании", "оферта", "правила",
        "разработка сайта", "продвижение сайта", "ответственная игра", "регламенты акций",
        "условия использования", "польз. соглашение", "мобильная версия", "правовая информация",
        "часто задаваемые вопросы", "возврат билетов", "места в городе", "гид выходного дня",
        "фирменный стиль", "подборки афиши", "google play", "app store", "корпоративный заказ",
        "корпоративным клиентам", "партнёрам и организаторам", "участие в исследованиях",
        "подарочные сертификаты", "пользовательское соглашение", "мастер-классы", "другой аккаунт",
        "оплата бонусами", "кешбэк до 20%", "возрастное ограничение 18+.", "приходите с другом",
        "выдадим вам карту аналогичного статуса", "условия розыгрыша", "супер игра", "время проведения:",

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

        # --- Адреса и контакты ---
        "8 (800) 200-55-39", "площадь победы, 1", "ул. октябрьская, 2/3",
        "+7 (4012) 555-200", "info@visit-kaliningrad.ru", "тиц ко",

        # --- Программа лояльности казино ---
        "правил посещения игорного заведения", "silver / серебро", "как получить карту",
        "выдается при достижении 5 000 бонусных баллов", "статус gold / золото",
        "выдается при достижении 40 000 бонусных баллов", "platinum / платина",
        "подробнее о программе лояльности", "только по приглашению",

        # --- Первые партии статичных названий городов afisha.ru ---
        "южно-сахалинск", "ханты-мансийск", "усолье-сибирское", "троицк (челябинск)",
        "спасск-дальний", "солнечногорск", "советская гавань", "славянск-на-кубани",
        "сергиев посад", "ростов-на-дону", "великий новгород", "большой камень",
        "благовещенск рб", "березовский (екатеринбург)", "анжеро-судженск",

        # --- Новая финальная партия статичных городов afisha.ru ---
        "ростов великий", "павловский посад", "орехово-зуево", "новый уренгой",
        "новочебоксарск", "новосергиевка", "нижний новгород", "нижневартовск",
        "набережные челны", "минеральные воды", "лодейное поле", "ликино-дулево",
        "лесной городок", "ленинградская", "краснокаменск", "краснознаменск",
        "козьмодемьянск", "великий устюг", "вышний волочек", "приморско-ахтарск"
    ]

    saved_count = 0

    for event in events_list:
        title = event["title"]
        title_lower = title.lower().strip()

        # === УРОВЕНЬ ФИЛЬТРАЦИИ 1: РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ (RegEx) ===
        # 1.1 Отсекаем динамические города со счетчиками (например, Тула33 события)
        if re.search(r'\d+\s*событ', title_lower) or re.search(r'\d+\s*рестор', title_lower):
            continue

            # 1.2 УМНЫЙ ГЕО-ФИЛЬТР: Отсекаем составные названия городов с дефисами,
        # уточнениями в скобках или приставками "на-", характерные для сквозного меню
        if re.search(r'\b\w+-\d+\b', title_lower) or \
                re.search(r'\w+-на-\w+', title_lower) or \
                re.search(r'\w+\s*\(калуга\)', title_lower) or \
                re.search(r'\w+\s*\(курск\)', title_lower) or \
                re.search(r'\w+\s*\(красноярск\)', title_lower) or \
                re.search(r'\w+\s*\(пенза\)', title_lower) or \
                re.search(r'\b(каменск|петропавловск|переславль|ленинск|верхняя)\b', title_lower):
            continue

        # === УРОВЕНЬ ФИЛЬТРАЦИИ 2: РАСШИРЕННЫЕ СТОП-СЛОВА ===
        if any(word in title_lower for word in stop_words):
            continue

        # Фильтр на минимальную длину заголовка мероприятия
        if len(title.strip()) < 10:
            continue

        try:
            # Запись строго по 4 стандартным колонкам, БЕЗ iso_date
            cursor.execute('''
                           INSERT OR IGNORE INTO events (title, date_info, category, source_url)
                VALUES (?, ?, ?, ?)
                           ''', (title, event["date_info"], event["category"], event["source"]))

            if cursor.rowcount > 0:
                saved_count += 1
                conn.commit()
        except Exception as e:
            print(f"❌ Ошибка записи события в БД: {e}")

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
