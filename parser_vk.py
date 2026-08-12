import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def parse_vk_motodvizh():
    """
    Автономный парсер через Selenium. Запускает скрытый браузер,
    заходит на стену группы и забирает свежие мото-события.
    """
    url = "https://vk.com"
    collected_events = []

    print("Инициализация скрытого браузера Selenium...")

    # Настраиваем браузер, чтобы он работал в фоновом режиме (без открытия окна на экране)
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Включаем фоновый режим
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Маскируемся под человека
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        # Запускаем браузер Chrome
        driver = webdriver.Chrome(options=chrome_options)
        print("Браузер успешно запущен. Переходим в группу Мотодвиж39...")

        driver.get(url)
        # Ждем 5 секунд, чтобы все скрипты ВК успели загрузить посты стены
        time.sleep(5)

        # Забираем готовый HTML-код страницы, который сформировал браузер
        html_content = driver.page_source
        driver.quit() # Закрываем браузер, он нам больше не нужен

        # Передаем код в BeautifulSoup для быстрого поиска
        soup = BeautifulSoup(html_content, 'html.parser')

        # В полной версии ВК каждый пост на стене лежит в блоке с классом 'post_capsule' или '_post'
        posts = soup.find_all('div', class_='_post')
        print(f"Найдено публикаций на стене группы: {len(posts)}")

        for post in posts:
            # Ищем текст внутри поста (в полной версии ВК это класс 'wall_post_text')
            text_block = post.find('div', class_='wall_post_text')
            if not text_block:
                continue

            post_text = text_block.text.strip()

            # Делаем аккуратный заголовок из первой строчки
            title_lines = post_text.split('\n')
            title = title_lines[0] if title_lines else "Мото мероприятие"
            if len(title) > 70:
                title = title[:70] + "..."

            # Формируем ссылку на конкретный пост.
            # ВК прячет ID поста в атрибут id самого блока (например, 'post-12345_6789')
            post_id_raw = post.get('id', '')
            if post_id_raw and 'post' in post_id_raw:
                post_url = f"https://vk.com{post_id_raw.replace('post', 'wall')}"
            else:
                post_url = url

            date_info = "Дата проведения указана внутри поста"

            # Ключевые слова для автоматического отбора мото-событий
            keywords = ["сбор", "старт", "выезд", "фестиваль", "открытие", "закрытие", "мото", "рок", "туса", "прохват"]
            is_event = any(word in post_text.lower() for word in keywords)

            if is_event:
                event_data = {
                    "title": title,
                    "date_info": date_info,
                    "category": "Мото тусовки",
                    "source": post_url
                }
                collected_events.append(event_data)

    except Exception as e:
        print(f"Ошибка при работе Selenium: {e}")

    return collected_events

def save_vk_events_to_db(events_list):
    conn = sqlite3.connect("afisha_database.db")
    cursor = conn.cursor()
    saved_count = 0
    for event in events_list:
        try:
            cursor.execute('''
                           INSERT OR IGNORE INTO events (title, date_info, category, source_url)
                VALUES (?, ?, ?, ?)
                           ''', (event["title"], event["date_info"], event["category"], event["source"]))
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"Ошибка записи ВК в БД: {e}")
    conn.commit()
    conn.close()
    print(f"В базу данных добавлено новых мото-событий: {saved_count}")

if __name__ == "__main__":
    vk_results = parse_vk_motodvizh()
    print(f"Отобрано целевых мото-мероприятий: {len(vk_results)}")
    if vk_results:
        save_vk_events_to_db(vk_results)
