import sqlite3
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Создаем само веб-приложение
app = FastAPI(title="Афиша Калининграда")

def get_all_events():
    """Функция вытаскивает все события из базы данных, сортируя их по дате"""
    conn = sqlite3.connect("afisha_database.db")
    cursor = conn.cursor()

    # Извлекаем название, детали, категорию и ссылку, сортируя от новых к старым
    cursor.execute("SELECT title, date_info, category, source_url FROM events ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()
    return rows

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Это главное 'окно' нашего сайта. Когда мы зайдем в браузер, выполнится этот код"""
    events = get_all_events()



    # Генерируем строки таблицы из данных нашей базы
    table_rows = ""
    for event in events:
        # В базе данных строка события — это кортеж (список) из 4 элементов:
        # event[0] - Название, event[1] - Дата, event[2] - Категория, event[3] - Ссылка
        table_rows += f"""
        <tr>
            <td>{event[0]}</td>
            <td>{event[1]}</td>
            <td><span class="badge">{event[2]}</span></td>
            <td><a href="{event[3]}" target="_blank">Перейти</a></td>
        </tr>
        """



    # HTML-код нашей страницы с красивым оформлением (CSS)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Афиша Калининграда</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f4f7f6; color: #333; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
            th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #2ecc71; color: white; text-transform: uppercase; font-size: 14px; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .badge {{ background-color: #34495e; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; }}
            a {{ color: #2980b9; text-decoration: none; font-weight: bold; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>📅 Сводная афиша мероприятий Калининграда</h1>
        <table>
            <thead>
                <tr>
                    <th>Название мероприятия</th>
                    <th>Дата / Время / Детали</th>
                    <th>Категория</th>
                    <th>Источник</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
