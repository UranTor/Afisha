import requests
from bs4 import BeautifulSoup

url = "https://gokaliningrad.com"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Подключаемся к сайту GoKaliningrad с новыми метками...")
response = requests.get(url, headers=headers)

if response.status_code == 200:
    print("Сайт успешно скачан! Начинаем разбор структуры...")
    soup = BeautifulSoup(response.text, 'html.parser')

    # Ищем все элементы, которые содержат названия заголовков карточек
    # Мы выяснили, что у них класс 'v-card__title'
    titles = soup.find_all('div', class_='v-card__title')

    print(f"Найдено заголовков событий на странице: {len(titles)}")
    print("-" * 40)

    # Перебираем все найденные заголовки
    for title_block in titles:
        # Извлекаем чистый текст названия (например, "Лолита")
        event_title = title_block.text.strip()

        # Теперь нам нужно найти дату. Внутри HTML-структуры этого сайта
        # блок с текстом/датой ('v-card__text') обычно идет сразу следующим за заголовком.
        # Мы просим Python: "Найди следующий элемент с классом v-card__text"
        parent_card = title_block.find_parent() # Поднимаемся на уровень всей карточки

        date_text = "Дата не указана"
        if parent_card:
            # Ищем блок текста внутри этой конкретной карточки
            text_block = parent_card.find('div', class_='v-card__text')
            if text_block:
                date_text = text_block.text.strip()

        print(f"Событие: {event_title}")
        print(f"Информация/Когда: {date_text}")
        print("-" * 40)
else:
    print("Не удалось загрузить сайт. Ошибка:", response.status_code)
