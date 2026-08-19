import os
import sqlite3
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

# Импортируем наш глобальный сборщик из соседнего файла scraper.py
from scraper import run_all_parsers

# НАСТРОЙКА ПУТИ: Автоматически вычисляем точный абсолютный путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "afisha_database.db")


async def auto_update_scheduler():
    """ Фоновый таймер обновлений (каждые 6 часов) """
    # Небольшая пауза на старте, чтобы база данных успела открыться
    await asyncio.sleep(5)

    while True:
        try:
            print("\n⏰ Фоновый таймер сработал! Начинаем автоматический сбор афиши...")
            run_all_parsers()
            print("⏰ Автоматический сбор успешно завершен. Следующий сбор через 6 часов.")
        except Exception as e:
            print(f"❌ Ошибка в работе фонового таймера: {e}")

        # Интервал ожидания 6 часов
        await asyncio.sleep(21600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """ Современный менеджер контекста для безопасного запуска фоновых задач """
    asyncio.create_task(auto_update_scheduler())
    print("🚀 Автоматический планировщик обновлений успешно запущен через Lifespan!")
    yield
    print("🛑 Приложение останавливается...")


# Инициализация приложения с подключением lifespan-менеджера
app = FastAPI(title="Афиша Калининграда", lifespan=lifespan)


def get_all_events():
    """ Получает события из базы данных по абсолютному пути """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Сортировка по умолчанию идет по id (новые выше)
    cursor.execute("SELECT title, date_info, category, source_url FROM events ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_sources():
    """ Получает список всех источников по абсолютному пути """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, url, category FROM sources")
    rows = cursor.fetchall()
    conn.close()
    return rows


@app.get("/", response_class=HTMLResponse)
def read_root():
    events = get_all_events()
    sources = get_all_sources()

    # 1. Генерируем строки таблицы событий
    table_rows = ""
    for event in events:
        table_rows += f"""
        <tr>
            <td>{event[0]}</td>
            <td>{event[1]}</td>
            <td><span class="badge">{event[2]}</span></td>
            <td><a href="{event[3]}" target="_blank">Перейти</a></td>
        </tr>
        """

    # 2. Генерируем список источников для админки
    source_rows = ""
    for src in sources:
        source_rows += f"""
        <tr>
            <td>{src[1]}</td>
            <td><code style="font-size:12px;">{src[2]}</code></td>
            <td>{src[3]}</td>
            <td><a href="/delete-source/{src[0]}" style="color:#e74c3c;">Удалить</a></td>
        </tr>
        """

    # Формирование HTML-страницы
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Афиша Калининграда</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background-color: #f4f7f6; color: #333; }}
            h1, h2 {{ color: #2c3e50; text-align: center; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden; margin-bottom: 50px; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background-color: #2ecc71; color: white; text-transform: uppercase; font-size: 13px; }}
            .source-th {{ background-color: #34495e; }}
            tr:hover {{ background-color: #fafafa; }}
            .badge {{ background-color: #9b59b6; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
            a {{ color: #2980b9; text-decoration: none; font-weight: bold; }}
            a:hover {{ text-decoration: underline; }}
            .admin-panel {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top: 50px; border-top: 4px solid #34495e; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #34495e; }}
            input[type="text"], select {{ width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
            button {{ background-color: #34495e; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold; }}
            button:hover {{ background-color: #2c3e50; }}
        </style>
    </head>
    <body>
        <div class="container">
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

            <div class="admin-panel">
                <h2>🛠️ Панель управления источниками данных</h2>
                
                <form action="/add-source" method="post" style="margin-bottom: 30px;">
                    <div class="form-group">
                        <label>Название источника:</label>
                        <input type="text" name="name" placeholder="Например: Афиша Клопс" required>
                    </div>
                    <div class="form-group">
                        <label>Ссылка (URL):</label>
                        <input type="text" name="url" placeholder="https://..." required>
                    </div>
                    <div class="form-group">
                        <label>Категория событий:</label>
                        <select name="category">
                            <option value="Общественное мероприятие">Общественное мероприятие</option>
                            <option value="Общественные мероприятия">Общественные мероприятия</option>
                            <option value="Мото тусовки">Мото тусовки</option>
                            <option value="Концерты">Концерты</option>
                            <option value="Концерты и праздники">Концерты и праздники</option>
                            <option value="Дискотеки и праздники">Дискотеки и праздники</option>
                        </select>
                    </div>
                    <button type="submit">➕ Добавить новый источник</button>
                </form>

                <h3>Текущие источники в базе данных:</h3>
                <table>
                    <thead>
                        <tr>
                            <th class="source-th">Название</th>
                            <th class="source-th">Ссылка (URL)</th>
                            <th class="source-th">Категория</th>
                            <th class="source-th">Действие</th>
                        </tr>
                    </thead>
                    <tbody>
                        {source_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/add-source")
def add_source(name: str = Form(...), url: str = Form(...), category: str = Form(...)):
    """ Добавление нового сайта-источника в базу через форму на сайте """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO sources (name, url, category) VALUES (?, ?, ?)",
            (name, url, category)
        )
        conn.commit()
    except Exception as e:
        print(f"Ошибка добавления: {e}")
    finally:
        conn.close()
    return RedirectResponse(url="/", status_code=303)


@app.get("/delete-source/{source_id}")
def delete_source(source_id: int):
    """ Удаление источника из базы данных """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        conn.commit()
    except Exception as e:
        print(f"Ошибка удаления: {e}")
    finally:
        conn.close()
    return RedirectResponse(url="/", status_code=303)
