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


# Этот блок нужен ТОЛЬКО для проверки файла на компьютере.
# Если запустить файл напрямую, он выполнит проверку и покажет результат.

if __name__ == "__main__":
    # 1. Собираем данные с сайта
    results = parse_gokaliningrad()
    print(f"\nУспешно собрано событий парсером: {len(results)}")

    # 2. Сохраняем их в нашу базу данных
    if results:
        save_events_to_db(results)
