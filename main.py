import os
import sqlite3
import asyncio
from pathlib import Path
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
    # Сортировка от ближайших дат к будущим
    cursor.execute("SELECT title, date_info, category, source_url FROM events ORDER BY iso_date ASC")
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
            /* МАКСИМАЛЬНО УВЕЛИЧЕННЫЙ ШРИФТ ДЛЯ ВЫСОКОЙ ЧИТАЕМОСТИ */
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px 40px; background-color: #f4f7f6; color: #333; font-size: 18px; }}
            h1 {{ color: #2c3e50; text-align: center; font-size: 32px; }}
            h2 {{ color: #2c3e50; text-align: center; font-size: 26px; }}
            .container {{ max-width: 1250px; margin: 0 auto; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden; margin-bottom: 25px; }}
            
            /* КРУПНЫЙ ШРИФТ В ЯЧЕЙКАХ С ЖЕСТКИМ МИНИМАЛЬНЫМ ОТСТУПОМ (padding 5px 12px) */
            th, td {{ padding: 5px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 18px; line-height: 1.4; }}
            
            /* ЗАГОЛОВКИ КОЛОНОК ТАБЛИЦЫ */
            th {{ background-color: #2ecc71; color: white; text-transform: uppercase; font-size: 19px; letter-spacing: 0.5px; }}
            .source-th {{ background-color: #34495e; }}
            tr:hover {{ background-color: #fafafa; }}
            
            /* КРУПНЫЕ БЕЙДЖИ КАТЕГОРИЙ */
            .badge {{ background-color: #9b59b6; color: white; padding: 4px 8px; border-radius: 4px; font-size: 14px; font-weight: bold; letter-spacing: 0.5px; }}
            a {{ color: #2980b9; text-decoration: none; font-weight: bold; font-size: 18px; }}
            a:hover {{ text-decoration: underline; }}
            
            .admin-panel {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top: 50px; border-top: 4px solid #34495e; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #34495e; font-size: 16px; }}
            input[type="text"], select {{ width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-size: 16px; }}
            button {{ background-color: #34495e; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; }}
            button:hover {{ background-color: #2c3e50; }}
            
            /* Стили для строки интерактивного поиска и календаря */
            .search-container {{ max-width: 100%; margin: 20px auto 10px auto; position: relative; }}
            .search-input {{ width: 100%; padding: 12px 20px; border: 2px solid #2ecc71; border-radius: 8px; font-size: 18px; box-sizing: border-box; box-shadow: 0 4px 6px rgba(0,0,0,0.02); outline: none; transition: border-color 0.3s; }}
            .search-input:focus {{ border-color: #27ae60; box-shadow: 0 4px 8px rgba(46, 204, 113, 0.2); }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📅 Сводная афиша мероприятий Калининграда</h1>
            
            <!-- СТРОКА ИНТЕРАКТИВНОГО ПОИСКА И КАЛЕНДАРЬ НА ОДНОЙ ЛИНИИ -->
            <div class="search-container" style="display: flex; gap: 15px;">
                <input type="text" id="liveSearch" class="search-input" placeholder="🔍 Начните вводить название мероприятия для моментальной фильтрации...">
                <input type="date" id="dateFilter" class="search-input" style="width: 280px; border-color: #34495e; cursor: pointer;" title="Выберите конкретную дату для вывода мероприятий">
            </div>
            
            <!-- ЕДИНСТВЕННАЯ ТАБЛИЦА МЕРОПРИЯТИЙ С ИДЕНТИФИКАТОРОМ ДЛЯ СКРИПТА -->
            <table id="eventsTable">
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

            <!-- АДМИН-ПАНЕЛЬ ИСТОЧНИКОВ -->
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
            
            <!-- НАЧАЛО БЛОКА ОБНОВЛЕННОГО СЧЕТЧИКА LIVEINTERNET (ЛЕВЫЙ КРАЙ) -->
            <div style="text-align: left; margin: 30px 0; padding-left: 15px;">
            <!--LiveInternet counter-->
            <a href="https://www.liveinternet.ru/click" target="_blank">
                <img id="licntB985" width="88" height="120" style="border:0" 
                     title="LiveInternet: показано количество просмотров и посетителей"
                     src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAEALAAAAAABAAEAAAIBTAA7" alt=""/>
            </a>
            <script>
                (function(d,s){{
                    d.getElementById("licntB985").src="https://counter.yadro.ru/hit?t28.12;r"+escape(d.referrer)+
                    ((typeof(s)=="undefined")?"":";s"+s.width+"*"+s.height+"*"+
                    (s.colorDepth?s.colorDepth:s.pixelDepth))+";u"+escape(d.URL)+
                    ";h"+escape(d.title.substring(0,150))+";"+Math.random()
                }})(document,screen)
            </script>
            <!--/LiveInternet-->
            </div>
            <!-- КОНЕЦ БЛОКА ОБНОВЛЕННОГО СЧЕТЧИКА LIVEINTERNET -->
            
            <!-- СКРИПТ КОМПЛЕКСНОЙ ФИЛЬТРАЦИИ ПО ТЕКСТУ И КАЛЕНДАРЮ -->
            <script>
                function filterTable() {{
                    let textFilter = document.getElementById('liveSearch').value.toLowerCase();
                    let dateFilter = document.getElementById('dateFilter').value; // Формат календаря: ГГГГ-ММ-ДД
                    let rows = document.querySelectorAll('#eventsTable tbody tr');
                    
                    rows.forEach(function(row) {{
                        let cells = row.getElementsByTagName('td');
                        if (cells.length > 0) {{
                            let titleCell = cells[0];
                            let detailsCell = cells[1];
                            
                            let titleText = titleCell.textContent || titleCell.innerText;
                            let detailsText = detailsCell.textContent || detailsCell.innerText;
                            
                            // 1. Проверка текстового поиска по названию
                            let textMatch = titleText.toLowerCase().indexOf(textFilter) > -1;
                            
                            // 2. Проверка фильтра даты
                            let dateMatch = true;
                            if (dateFilter) {{
                                // Конвертируем дату ГГГГ-ММ-ДД в русскую строку (например: "24 октября")
                                let options = {{ day: 'numeric', month: 'long' }};
                                let parsedDate = new Date(dateFilter).toLocaleDateString('ru-RU', options);
                                
                                // Проверяем вхождение дня в текстовую колонку деталей
                                dateMatch = detailsText.toLowerCase().indexOf(parsedDate.toLowerCase()) > -1;
                            }}
                            
                            // Отображаем строку, только если совпали оба фильтра одновременно
                            if (textMatch && dateMatch) {{
                                row.style.display = '';
                            }} else {{
                                row.style.display = 'none';
                            }}
                        }}
                    }});
                }}

                // Привязываем функцию комплексного отсева к обоим инпутам управления
                document.getElementById('liveSearch').addEventListener('keyup', filterTable);
                document.getElementById('dateFilter').addEventListener('change', filterTable);
            </script>
            
        </div>
    </body>
    </html>
    """

        output_file = Path(__file__).resolve().parent / "index.html"
        output_file.write_text(html_content, encoding="utf-8")

        return HTMLResponse(content=html_content)


@app.post("/add-source")
def add_source(name: str = Form(...), url: str = Form(...), category: str = Form(...)):
    """ Добавление нового сайта-источника в базу через форму на сайте """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # ИСПРАВЛЕНИЕ: Явно передаем is_active = 1, чтобы новый источник сразу вставал в строй
        cursor.execute(
            "INSERT OR IGNORE INTO sources (name, url, category, is_active) VALUES (?, ?, ?, 1)",
            (name, url, category)
        )
        conn.commit()
    except Exception as e:
        print(f"Ошибка добавления источника: {e}")
    finally:
        conn.close()

    # ИСПРАВЛЕНИЕ: Используем статус 303 (See Other) для корректного перенаправления в FastAPI
    return RedirectResponse(url="/", status_code=303)


@app.get("/delete-source/{source_id}")
def delete_source(source_id: int):
    """ Удаление источника из базы данных по его ID """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        conn.commit()
    except Exception as e:
        print(f"Ошибка удаления источника: {e}")
    finally:
        conn.close()

    return RedirectResponse(url="/", status_code=303)