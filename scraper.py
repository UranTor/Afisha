import requests
from bs4 import BeautifulSoup

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


def save_events_to_db(events_list):
    """
    Функция берет список словарей, который собрал парсер,
    и записывает каждое событие в базу данных SQLite.
    """
    import sqlite3
    conn = sqlite3.connect("afisha_database.db")
    cursor = conn.cursor()

    saved_count = 0

    for event in events_list:
        try:
            # INSERT OR IGNORE защищает от дубликатов.
            # Если событие с таким названием и датой уже есть, база его пропустит.
            cursor.execute('''
                           INSERT OR IGNORE INTO events (title, date_info, category, source_url)
                VALUES (?, ?, ?, ?)
                           ''', (event["title"], event["date_info"], event["category"], event["source"]))

            # Если запись действительно добавлена, увеличиваем счетчик
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"Ошибка записи события в БД: {e}")

    conn.commit()
    conn.close()
    print(f"Запись завершена. В базу данных добавлено новых событий: {saved_count}")





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






if __name__ == "__main__":
    # --- 1. ЗАПУСК ПАРСЕРА №1 (GoKaliningrad) ---
    go_results = parse_gokaliningrad()
    print(f"GoKaliningrad собрал: {len(go_results)} событий")
    if go_results:
        save_events_to_db(go_results) # Наша старая функция записи в БД

    print("-" * 50)

    # --- 2. ЗАПУСК ПАРСЕРА №2 (Казино Собрание) ---
    casino_results = parse_casino_sobranie()
    print(f"Казино Собрание собрало: {len(casino_results)} событий")
    if casino_results:
        save_events_to_db(casino_results)
