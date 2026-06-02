from flask import Flask, render_template
import requests
from datetime import datetime

app = Flask(__name__)

# Ссылка на публичный API Московской Биржи (акции в режиме торгов Т+ Основной ход)
MOEX_API_URL = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?iss.meta=off"

@app.route('/')
def index():
    try:
        # Отправляем запрос к API Мосбиржи
        response = requests.get(MOEX_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Извлекаем таблицы метаданных и рыночных котировок
        securities_data = data.get("securities", {})
        marketdata_data = data.get("marketdata", {})
        
        sec_columns = securities_data.get("columns", [])
        sec_rows = securities_data.get("data", [])
        
        market_columns = marketdata_data.get("columns", [])
        market_rows = marketdata_data.get("data", [])
        
        # Находим индексы необходимых колонок для базовой информации
        secid_idx = sec_columns.index("SECID")
        name_idx = sec_columns.index("SHORTNAME")
        prev_price_idx = sec_columns.index("PREVPRICE")
        
        # Находим индексы колонок текущих торгов
        m_secid_idx = market_columns.index("SECID")
        last_idx = market_columns.index("LAST")      # Последняя цена сделки
        change_idx = market_columns.index("CHANGE")  # Изменение цены за день
        
        # Создаем карту базовых данных для быстрого поиска по тикеру
        sec_map = {row[secid_idx]: {"name": row[name_idx], "prev": row[prev_price_idx]} for row in sec_rows}
        
        # Список акций (тикеры) для вывода на дашборд
        target_stocks = ['SBER', 'GAZP', 'LKOH', 'YNDX', 'NVTK', 'ROSN', 'VTBR', 'TATN']
        processed_stocks = []
        
        for row in market_rows:
            secid = row[m_secid_idx]
            if secid in target_stocks:
                current_price = row[last_idx]
                
                # Если торги по акции сегодня еще не проводились, берем цену закрытия прошлого дня
                if current_price is None:
                    current_price = sec_map[secid]["prev"]
                    change = 0.0
                else:
                    change = row[change_idx] if row[change_idx] is not None else 0.0
                
                processed_stocks.append({
                    "ticker": secid,
                    "name": sec_map[secid]["name"],
                    "value": round(current_price, 2) if current_price else 0.0,
                    "change": round(change, 2)
                })
        
        # Сортируем акции в алфавитном порядке тикеров
        processed_stocks.sort(key=lambda x: x['ticker'])
        
        current_date = datetime.now().strftime("%d.%m.%Y в %H:%M")
        return render_template('index.html', stocks=processed_stocks, date=current_date)
        
    except Exception as e:
        # Перехват сетевых сбоев и ошибок парсинга
        return render_template('index.html', error=f"Не удалось загрузить котировки акций: {e}")

if __name__ == '__main__':
    app.run(debug=True)