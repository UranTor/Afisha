import requests
from bs4 import BeautifulSoup
import sqlite3  # <- ДОБАВЛЯЕМ ЭТУ СТРОКУ


def parse_gokaliningrad():
    """
    Это функция. Она объединяет наш старый код в одну готовую команду.
    Вместо вывода на экран (print), она будет возвращать собранные данные.
    """
    url = "https://gokaliningrad.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Сюда мы будем складывать результаты в чистом виде
    collected_events = []

    print("Парсер GoKaliningrad запущен...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Ошибка загрузки GoKaliningrad: {response.status_code}")
            return collected_events

        soup = BeautifulSoup(response.text, 'html.parser')
        titles = soup.find_all('div', class_='v-card__title')

        for title_block in titles:
            event_title = title_block.text.strip()
            parent_card = title_block.find_parent()

            date_text = "Дата не указана"
            if parent_card:
                text_block = parent_card.find('div', class_='v-card__text')
                if text_block:
                    # Исправление: get_text разделяет слипшиеся слова красивой чертой
                    date_text = text_block.get_text(separator=" | ", strip=True)

            # Вместо print мы создаем "пакет данных" (словарь) для каждого события
            event_data = {
                "title": event_title,
                "date_info": date_text,
                "category": "Общественное мероприятие", # Базовая категория для этого сайта
                "source": url
            }
            # Кладем этот пакет в наш общий список
            collected_events.append(event_data)

    except Exception as e:
        print(f"Произошла непредвиденная ошибка при парсинге: {e}")

    return collected_events


def parse_casino_sobranie():
    """
    Обновленный парсер официального сайта казино 'Собрание'.
    Ищет события в элементах списков афиши.
    """
    url = "https://www.sobranie-casino.com/ru/current/all/"
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

        # На сайте казино элементы афиши выводятся в виде списков.
        # Проверяем все возможные варианты карточек на этом движке сайта.
        event_items = soup.find_all('li', class_='events-list__item') or \
                      soup.find_all('a', class_='events-list__item') or \
                      soup.find_all('div', class_='events-item')

        print(f"Найдено сырых блоков афиши: {len(event_items)}")

        for item in event_items:
            # Ищем название (оно лежит в блоке с классом, содержащим 'title')
            title_block = item.find(class_='events-item__title') or \
                          item.find(class_='title') or \
                          item.find('h3')

            # Ищем дату (класс, содержащий 'date')
            date_block = item.find(class_='events-item__date') or \
                         item.find(class_='date') or \
                         item.find(class_='events-item__time')

            if title_block:
                title = title_block.text.strip()
                # Пропускаем пустые или системные строки
                if not title:
                    continue

                date_text = date_block.text.strip() if date_block else "Дата на сайте казино"
                # Заменяем внутренние переходы строк на аккуратные пробелы
                date_text = " ".join(date_text.split())

                collected_events.append({
                    "title": title,
                    "date_info": date_text,
                    "category": "Дискотеки и праздники",
                    "source": url
                })

        # Если списки не нашлись, делаем аварийный сбор по всем ссылкам с деталями
        if not collected_events:
            for link in soup.find_all('a', href=True):
                if '/event/' in link['href']:
                    title = link.text.strip()
                    if title and len(title) > 5:
                        collected_events.append({
                            "title": "Мероприятие: " + " ".join(title.split()),
                            "date_info": "Уточняйте на сайте",
                            "category": "Дискотеки и праздники",
                            "source": url
                        })

    except Exception as e:
        print(f"Ошибка при парсинге Казино Собрание: {e}")

    return collected_events


def parse_klops_afisha():
    """
    Максимально открытый парсер Клопс Афиши.
    Собирает любые текстовые ссылки со страницы афиши.
    """
    url = "https://klops.ru/afisha"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    collected_events = []
    print("Парсер Клопс Афиши запущен...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Ошибка загрузки Клопс: {response.status_code}")
            return collected_events

        soup = BeautifulSoup(response.text, 'html.parser')

        # Берем вообще все ссылки на странице
        for link in soup.find_all('a', href=True):
            title = link.text.strip()
            href = link['href']

            # Отбираем только те ссылки, текст которых длиннее 15 символов
            # (это гарантирует, что мы берем названия событий, а не пункты меню "Вход", "Новости")
            if title and len(title) > 15:
                # Исключаем служебные фразы
                if any(word in title.lower() for word in ["купить билет", "все концерты", "политика", "контакты"]):
                    continue

                clean_title = " ".join(title.split())
                full_url = href if href.startswith('http') else "https://klops.ru" + href

                collected_events.append({
                    "title": clean_title,
                    "date_info": "Уточняйте на Klops.ru",
                    "category": "Концерты и праздники",
                    "source": full_url
                })

        # Удаляем дубликаты
        unique_events = []
        titles_seen = set()
        for ev in collected_events:
            if ev["title"] not in titles_seen:
                titles_seen.add(ev["title"])
                unique_events.append(ev)

        return unique_events

    except Exception as e:
        print(f"Ошибка при парсинге Клопс Афиши: {e}")
    return collected_events


def parse_afisha_80let():
    """
    Универсальный парсер для туристического портала visit-kaliningrad.ru / афиши 80 лет.
    """
    url = "https://visit-kaliningrad.ru"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    collected_events = []
    print("Парсер Афиши 80 лет области запущен...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Ошибка загрузки Афиши области: {response.status_code}")
            return collected_events

        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем ссылки, в адресе которых есть маркеры событий
        for link in soup.find_all('a', href=True):
            title = link.text.strip()
            href = link['href']

            if title and len(title) > 12:
                if any(word in title.lower() for word in ["карта", "маршруты", "о нас", "контакты", "назад"]):
                    continue

                clean_title = " ".join(title.split())
                full_url = href if href.startswith('http') else "https://visit-kaliningrad.ru" + href

                collected_events.append({
                    "title": clean_title,
                    "date_info": "Смотрите на visit-kaliningrad.ru",
                    "category": "Общественные мероприятия",
                    "source": full_url
                })

        unique_events = []
        titles_seen = set()
        for ev in collected_events:
            if ev["title"] not in titles_seen:
                titles_seen.add(ev["title"])
                unique_events.append(ev)

        return unique_events

    except Exception as e:
        print(f"Ошибка при парсинге Афиши области: {e}")
    return collected_events


def parse_casino_shambala():
    """
    Парсер официального сайта казино 'Шамбала' (Калининград).
    Собирает шоу-программы, концерты и дискотеки выходного дня.
    """
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

        # На сайте Шамбалы анонсы обычно содержатся в тегах h2, h3
        # или блоках с описанием мероприятий. Применим сбор по текстовым ссылкам и заголовкам
        for block in soup.find_all(['h2', 'h3', 'a']):
            title = block.text.strip()

            # Отбираем содержательные названия мероприятий длиннее 15 символов
            if title and len(title) > 15 and len(title) < 100:
                # Исключаем элементы навигации сайта
                if any(word in title.lower() for word in ["главная", "контакты", "оферта", "правила", "казино", "о нас"]):
                    continue

                clean_title = " ".join(title.split())

                collected_events.append({
                    "title": clean_title,
                    "date_info": "Выходные дни / Уточняйте на сайте",
                    "category": "Дискотеки и праздники",
                    "source": url
                })

        # Удаляем дубликаты
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


def save_events_to_db(events_list):
    """
    Функция берет список словарей, который собрал парсер,
    и записывает каждое событие в базу данных SQLite.
    """
    conn = sqlite3.connect("afisha_database.db")
    cursor = conn.cursor()

    saved_count = 0

    for event in events_list:
        try:
            # INSERT OR IGNORE защищает от дубликатов.
            cursor.execute('''
                           INSERT OR IGNORE INTO events (title, date_info, category, source_url)
                VALUES (?, ?, ?, ?)
                           ''', (event["title"], event["date_info"], event["category"], event["source"]))

            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"Ошибка записи события в БД: {e}")

    conn.commit()
    conn.close()
    print(f"Запись завершена. В базу данных добавлено новых событий: {saved_count}")


def run_all_parsers():
    """
    Главный диспетчер. Он опрашивает базу данных, находит активные источники
    и автоматически распределяет, какого робота запустить для каждого сайта.
    """
    print("\n=== ЗАПУСК ГЛОБАЛЬНОГО СБОРЩИКА АФИШИ ===")

    conn = sqlite3.connect("afisha_database.db")
    cursor = conn.cursor()
    # Берем только активные источники (где is_active = 1)
    cursor.execute("SELECT name, url FROM sources WHERE is_active = 1")
    active_sources = cursor.fetchall()
    conn.close()

    print(f"В базе данных найдено активных источников для проверки: {len(active_sources)}")
    print("=" * 40)

    for name, url in active_sources:
        print(f"\nПроверяем источник: {name} ({url})")
        results = []

        # Умная развилка: анализируем адрес сайта и вызываем нужную функцию
        if "gokaliningrad.com" in url:
            results = parse_gokaliningrad()
        elif "sobranie-casino.com" in url:
            results = parse_casino_sobranie()
        elif "afisha80let" in url or "visit-kaliningrad.ru" in url:
            results = parse_afisha_80let()
        elif "klops.ru" in url:
            results = parse_klops_afisha()
        elif "shambala" in url:
            results = parse_casino_shambala()



        else:
            print(f"⚠️ Для сайта {name} еще не написан точный парсер. Запускаем базовый сбор.")
            # Сюда в будущем можно поставить универсальный парсер
            continue

        print(f"-> Собрано событий: {len(results)}")
        if results:
            save_events_to_db(results)







if __name__ == "__main__":
    # Теперь при запуске файла scraper.py автоматически выполнится весь цикл сбора по базе данных!
    run_all_parsers()

