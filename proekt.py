import requests
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template_string, jsonify, make_response, request

app = Flask(__name__)

# Хранилище данных для текущих курсов
price_history = {
    'EUR/USD': [],
    'GBP/USD': [],
    'JPY/USD': [],
    'CNY/USD': [],
    'AUD/USD': [],
    'CAD/USD': [],
    'CHF/USD': [],
    'Gold (USD/oz)': [],
    'Silver (USD/oz)': [],
    'Copper (USD/lb)': [],
    'Aluminum (USD/t)': [],
    'Tin (USD/t)': []
}

# Исторические данные по годам
historical_rates = {
    'EUR/USD': {2000: 0.85, 2005: 0.80, 2010: 0.75, 2015: 0.90, 2020: 1.14, 2024: 1.09},
    'GBP/USD': {2000: 0.66, 2005: 0.55, 2010: 0.65, 2015: 0.65, 2020: 0.75, 2024: 0.79},
    'JPY/USD': {2000: 108, 2005: 110, 2010: 93, 2015: 121, 2020: 106, 2024: 150},
    'CNY/USD': {2000: 8.28, 2005: 8.07, 2010: 6.77, 2015: 6.20, 2020: 6.90, 2024: 7.25},
    'AUD/USD': {2000: 0.55, 2005: 0.75, 2010: 0.95, 2015: 0.75, 2020: 0.70, 2024: 0.66},
    'CAD/USD': {2000: 0.65, 2005: 0.85, 2010: 1.00, 2015: 0.78, 2020: 0.75, 2024: 0.74},
    'CHF/USD': {2000: 0.69, 2005: 0.80, 2010: 1.08, 2015: 0.98, 2020: 0.91, 2024: 0.89},
    'Gold (USD/oz)': {2000: 280, 2005: 450, 2010: 1220, 2015: 1100, 2020: 1850, 2024: 2650},
    'Silver (USD/oz)': {2000: 5.0, 2005: 7.5, 2010: 18.0, 2015: 14.0, 2020: 22.0, 2024: 30.5},
    'Copper (USD/lb)': {2000: 0.85, 2005: 1.45, 2010: 3.40, 2015: 2.50, 2020: 2.80, 2024: 4.35},
    'Aluminum (USD/t)': {2000: 1600, 2005: 1900, 2010: 2400, 2015: 1700, 2020: 1700, 2024: 2600},
    'Tin (USD/t)': {2000: 5200, 2005: 7500, 2010: 20000, 2015: 16000, 2020: 17000, 2024: 33000}
}

# Флаг для фонового обновления
updating = True

def get_metal_prices():
    """Получение цен на металлы через API"""
    try:
        response = requests.get('https://api.metals.live/v1/spot', timeout=10)
        if response.status_code == 200:
            data = response.json()
            metals = {}
            for item in data:
                if item.get('metal') == 'Gold':
                    metals['gold'] = float(item.get('price', 0))
                elif item.get('metal') == 'Silver':
                    metals['silver'] = float(item.get('price', 0))
                elif item.get('metal') == 'Copper':
                    metals['copper'] = float(item.get('price', 0))
            return metals
    except:
        pass
    
    # Резервные данные
    return {
        'gold': 2650.50,
        'silver': 30.25,
        'copper': 4.35,
        'aluminum': 2600.00,
        'tin': 33000.00
    }

def initialize_with_backup_data():
    """Инициализация резервными данными"""
    current_time = datetime.now()
    time_str = current_time.strftime('%H:%M:%S')
    
    backup_data = {
        'EUR/USD': 1.0850,
        'GBP/USD': 1.2650,
        'JPY/USD': 110.50,
        'CNY/USD': 7.2450,
        'AUD/USD': 0.6580,
        'CAD/USD': 0.7360,
        'CHF/USD': 0.8920,
        'Gold (USD/oz)': 2650.50,
        'Silver (USD/oz)': 30.25,
        'Copper (USD/lb)': 4.350,
        'Aluminum (USD/t)': 2600,
        'Tin (USD/t)': 33000
    }
    
    for currency, rate in backup_data.items():
        price_history[currency].append({'time': time_str, 'price': rate})

def update_prices():
    """Фоновое обновление курсов валют и металлов"""
    global updating
    last_update = None
    
    while updating:
        try:
            # 1. Получение курсов валют
            response = requests.get('https://open.er-api.com/v6/latest/USD', timeout=5)
            data = response.json()
            
            current_time = datetime.now()
            
            if last_update is None or (current_time - last_update).seconds >= 60:
                # Валюты к USD
                eur_usd = 1 / data['rates']['EUR'] if 'EUR' in data['rates'] else 0.92
                gbp_usd = 1 / data['rates']['GBP'] if 'GBP' in data['rates'] else 0.79
                jpy_usd = data['rates']['JPY'] if 'JPY' in data['rates'] else 110
                cny_usd = data['rates']['CNY'] if 'CNY' in data['rates'] else 7.2
                aud_usd = 1 / data['rates']['AUD'] if 'AUD' in data['rates'] else 0.65
                cad_usd = 1 / data['rates']['CAD'] if 'CAD' in data['rates'] else 0.73
                chf_usd = 1 / data['rates']['CHF'] if 'CHF' in data['rates'] else 0.89
                
                # 2. Получение цен на металлы
                metal_prices = get_metal_prices()
                
                # Добавляем валюты
                price_history['EUR/USD'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(eur_usd, 4)})
                price_history['GBP/USD'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(gbp_usd, 4)})
                price_history['JPY/USD'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(jpy_usd, 2)})
                price_history['CNY/USD'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(cny_usd, 4)})
                price_history['AUD/USD'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(aud_usd, 4)})
                price_history['CAD/USD'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(cad_usd, 4)})
                price_history['CHF/USD'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(chf_usd, 4)})
                
                # Добавляем металлы
                price_history['Gold (USD/oz)'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(metal_prices.get('gold', 2650.50), 2)})
                price_history['Silver (USD/oz)'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(metal_prices.get('silver', 30.25), 2)})
                price_history['Copper (USD/lb)'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(metal_prices.get('copper', 4.35), 3)})
                price_history['Aluminum (USD/t)'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(metal_prices.get('aluminum', 2600.00), 0)})
                price_history['Tin (USD/t)'].append({'time': current_time.strftime('%H:%M:%S'), 'price': round(metal_prices.get('tin', 33000.00), 0)})
                
                # Ограничиваем историю 20 записями
                for key in price_history:
                    if len(price_history[key]) > 20:
                        price_history[key] = price_history[key][-20:]
                
                last_update = current_time
                
            # Заполняем начальными данными если пусто
            if len(price_history['EUR/USD']) == 1:
                for _ in range(10):
                    for key in price_history:
                        if price_history[key]:
                            price_history[key].append(price_history[key][0].copy())
                        
        except Exception as e:
            print(f"Ошибка обновления: {e}")
            if not any(price_history.values()):
                initialize_with_backup_data()
        
        time.sleep(30)

# HTML шаблон для главной страницы с текущими курсами
MAIN_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Курсы валют и цены на металлы к USD - Котировки онлайн</title>
    <meta name="description" content="Актуальные курсы валют и цены на металлы к доллару США. Исторические данные с 2000 года.">
    <meta name="keywords" content="курс валют, доллар США, евро, цена золота, исторические данные">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; margin: 20px 0; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .nav-links {
            text-align: center;
            margin: 20px 0;
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        .nav-button {
            background: rgba(255,215,0,0.2);
            border: 2px solid #ffd700;
            color: #ffd700;
            padding: 10px 20px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .nav-button:hover {
            background: #ffd700;
            color: #1e3c72;
            transform: translateY(-2px);
        }
        .usd-badge { display: inline-block; background: linear-gradient(135deg, #ffd700, #ffb700); color: #1e3c72; padding: 5px 15px; border-radius: 20px; font-size: 0.5em; font-weight: bold; margin-left: 10px; vertical-align: middle; }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(650px, 1fr)); gap: 20px; margin-top: 30px; }
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s ease;
        }
        .card:hover { transform: translateY(-5px); }
        .card h2 { margin-bottom: 15px; font-size: 1.8em; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
        .current-price { font-size: 1.5em; font-weight: bold; color: #ffd700; }
        .price-inverse { margin-top: 5px; font-size: 0.9em; color: #a0c4ff; }
        .stats {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            padding: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            flex-wrap: wrap;
        }
        .stats div { text-align: center; flex: 1; min-width: 80px; padding: 5px; }
        .stats span { display: block; font-size: 0.9em; color: #ccc; margin-bottom: 5px; }
        .stats strong { font-size: 1.2em; color: #fff; }
        .update-time { text-align: center; margin-top: 20px; font-size: 0.9em; opacity: 0.8; }
        .loading { text-align: center; padding: 40px; font-size: 1.2em; }
        .market-status { text-align: center; margin: 10px 0; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #4caf50; margin-right: 5px; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
        @media (max-width: 768px) { .dashboard { grid-template-columns: 1fr; } h1 { font-size: 1.8em; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>💵 Котировки к доллару США <span class="usd-badge">USD</span></h1>
        <div class="nav-links">
            <a href="/" class="nav-button">📊 Текущие курсы</a>
            <a href="/historical" class="nav-button">📈 Исторические данные (2000-2024)</a>
        </div>
        <div class="market-status"><span class="status-indicator"></span> Обновление каждую минуту</div>
        <div id="dashboard" class="dashboard"><div class="loading">Загрузка данных...</div></div>
        <div class="update-time" id="updateTime"></div>
    </div>
    
    <script>
        function updateDashboard() {
            fetch('/api/prices')
                .then(response => response.json())
                .then(data => {
                    const dashboard = document.getElementById('dashboard');
                    if (data.error) { dashboard.innerHTML = '<div class="loading">Ошибка загрузки данных</div>'; return; }
                    
                    dashboard.innerHTML = '';
                    
                    const items = {
                        'EUR/USD': { name: 'Евро', base: '€', unit: '' },
                        'GBP/USD': { name: 'Британский фунт', base: '£', unit: '' },
                        'JPY/USD': { name: 'Японская йена', base: '¥', unit: '' },
                        'CNY/USD': { name: 'Китайский юань', base: '¥', unit: '' },
                        'AUD/USD': { name: 'Австралийский доллар', base: 'A$', unit: '' },
                        'CAD/USD': { name: 'Канадский доллар', base: 'C$', unit: '' },
                        'CHF/USD': { name: 'Швейцарский франк', base: 'CHF', unit: '' },
                        'Gold (USD/oz)': { name: 'Золото', base: '', unit: '/тр. унция' },
                        'Silver (USD/oz)': { name: 'Серебро', base: '', unit: '/тр. унция' },
                        'Copper (USD/lb)': { name: 'Медь', base: '', unit: '/фунт' },
                        'Aluminum (USD/t)': { name: 'Алюминий', base: '', unit: '/тонна' },
                        'Tin (USD/t)': { name: 'Олово', base: '', unit: '/тонна' }
                    };
                    
                    Object.keys(data.pairs).forEach(pair => {
                        const pairData = data.pairs[pair];
                        const info = items[pair] || { name: pair, base: '', unit: '' };
                        const card = document.createElement('div');
                        card.className = 'card';
                        
                        const changeSign = pairData.change >= 0 ? '+' : '';
                        
                        let inversePrice = '';
                        if (pair === 'JPY/USD') inversePrice = `1 USD = ${(1/pairData.current).toFixed(2)} JPY`;
                        if (pair === 'AUD/USD') inversePrice = `1 USD = ${(1/pairData.current).toFixed(4)} AUD`;
                        if (pair === 'CAD/USD') inversePrice = `1 USD = ${(1/pairData.current).toFixed(4)} CAD`;
                        if (pair === 'CHF/USD') inversePrice = `1 USD = ${(1/pairData.current).toFixed(4)} CHF`;
                        
                        card.innerHTML = `
                            <h2>
                                ${info.base} ${info.name}
                                <span class="current-price">${pairData.current.toFixed(pair.includes('Silver')?2:(pair.includes('Aluminum')||pair.includes('Tin')?0:(pair.includes('Copper')?3:4)))}${info.unit}</span>
                            </h2>
                            ${inversePrice ? `<div class="price-inverse">📊 ${inversePrice}</div>` : ''}
                            <div id="chart-${pair.replace(/[ /()]/g, '-')}" style="height: 300px;"></div>
                            <div class="stats">
                                <div><span>📉 Мин.</span><strong>${pairData.min.toFixed(pair.includes('Silver')?2:(pair.includes('Aluminum')||pair.includes('Tin')?0:(pair.includes('Copper')?3:4)))}</strong></div>
                                <div><span>📈 Макс.</span><strong>${pairData.max.toFixed(pair.includes('Silver')?2:(pair.includes('Aluminum')||pair.includes('Tin')?0:(pair.includes('Copper')?3:4)))}</strong></div>
                                <div><span>📊 Изм.</span><strong style="color: ${pairData.change >= 0 ? '#4caf50' : '#f44336'}">${changeSign}${pairData.change.toFixed(4)}</strong></div>
                                <div><span>💱 Спред</span><strong>${(pairData.max - pairData.min).toFixed(pair.includes('Silver')?2:(pair.includes('Aluminum')||pair.includes('Tin')?0:(pair.includes('Copper')?3:4)))}</strong></div>
                            </div>
                        `;
                        dashboard.appendChild(card);
                        
                        const plotData = [{
                            x: pairData.history.map(h => h.time),
                            y: pairData.history.map(h => h.price),
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: pair,
                            line: { color: '#ffd700', width: 3 },
                            marker: { color: '#ff6b6b', size: 8 },
                            fill: 'tozeroy',
                            fillcolor: 'rgba(255, 215, 0, 0.1)'
                        }];
                        const layout = {
                            plot_bgcolor: 'rgba(0,0,0,0)', paper_bgcolor: 'rgba(0,0,0,0)',
                            font: { color: '#fff' }, margin: { t: 10, r: 10, b: 40, l: 60 },
                            xaxis: { title: 'Время' },
                            yaxis: { title: `USD${info.unit}` },
                            hovermode: 'x unified'
                        };
                        Plotly.newPlot(`chart-${pair.replace(/[ /()]/g, '-')}`, plotData, layout, { responsive: true, displaylogo: false });
                    });
                    document.getElementById('updateTime').textContent = `🕐 Последнее обновление: ${data.last_update}`;
                })
                .catch(error => console.error('Ошибка:', error));
        }
        updateDashboard();
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>
'''

# HTML шаблон для страницы с историческими данными
HISTORICAL_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Исторические курсы валют и металлов 2000-2024</title>
    <meta name="description" content="Исторические данные курсов валют и цен на металлы с 2000 по 2024 год. Анализ динамики и графики.">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; margin: 20px 0; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .nav-links {
            text-align: center;
            margin: 20px 0;
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        .nav-button {
            background: rgba(255,215,0,0.2);
            border: 2px solid #ffd700;
            color: #ffd700;
            padding: 10px 20px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .nav-button:hover {
            background: #ffd700;
            color: #1e3c72;
        }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(650px, 1fr)); gap: 20px; margin-top: 30px; }
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        .card h2 { margin-bottom: 15px; font-size: 1.8em; text-align: center; }
        .stats-table {
            margin-top: 15px;
            width: 100%;
            border-collapse: collapse;
        }
        .stats-table td {
            padding: 8px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        .stats-table td:first-child { font-weight: bold; }
        .positive { color: #4caf50; }
        .negative { color: #f44336; }
        .info-text {
            text-align: center;
            margin: 20px;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
        }
        @media (max-width: 768px) { .dashboard { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 Исторические данные (2000-2024)</h1>
        <div class="nav-links">
            <a href="/" class="nav-button">📊 Текущие курсы</a>
            <a href="/historical" class="nav-button">📈 Исторические данные</a>
        </div>
        <div class="info-text">
            📊 Динамика курсов валют и цен на металлы с 2000 по 2024 год
        </div>
        <div id="historical-dashboard" class="dashboard">
            <div class="loading">Загрузка исторических данных...</div>
        </div>
    </div>
    
    <script>
        const historicalData = {{ historical_data|tojson }};
        const itemsInfo = {
            'EUR/USD': { name: 'Евро', unit: '', color: '#ffd700' },
            'GBP/USD': { name: 'Британский фунт', unit: '', color: '#ff6b6b' },
            'JPY/USD': { name: 'Японская йена', unit: '', color: '#4ecdc4' },
            'CNY/USD': { name: 'Китайский юань', unit: '', color: '#95e77e' },
            'AUD/USD': { name: 'Австралийский доллар', unit: '', color: '#ff9ff3' },
            'CAD/USD': { name: 'Канадский доллар', unit: '', color: '#feca57' },
            'CHF/USD': { name: 'Швейцарский франк', unit: '', color: '#48dbfb' },
            'Gold (USD/oz)': { name: 'Золото', unit: ' $/унц', color: '#f9ca24' },
            'Silver (USD/oz)': { name: 'Серебро', unit: ' $/унц', color: '#e1b12c' },
            'Copper (USD/lb)': { name: 'Медь', unit: ' $/фунт', color: '#d63031' },
            'Aluminum (USD/t)': { name: 'Алюминий', unit: ' $/т', color: '#a29bfe' },
            'Tin (USD/t)': { name: 'Олово', unit: ' $/т', color: '#6c5ce7' }
        };
        
        const dashboard = document.getElementById('historical-dashboard');
        dashboard.innerHTML = '';
        
        Object.keys(historicalData).forEach(pair => {
            const data = historicalData[pair];
            const info = itemsInfo[pair] || { name: pair, unit: '', color: '#ffd700' };
            
            const years = Object.keys(data).sort();
            const values = years.map(y => data[y]);
            const firstValue = values[0];
            const lastValue = values[values.length - 1];
            const change = lastValue - firstValue;
            const changePercent = (change / firstValue * 100).toFixed(1);
            
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = `
                <h2>${pair} <span style="font-size:0.6em;">${info.name}</span></h2>
                <div id="chart-hist-${pair.replace(/[ /()]/g, '-')}" style="height: 300px;"></div>
                <table class="stats-table">
                    <tr><td>2000</td><td>${years.includes('2000') ? data['2000'].toFixed(2) : '-'}</td>
                        <td>2010</td><td>${years.includes('2010') ? data['2010'].toFixed(2) : '-'}</td>
                        <td>2020</td><td>${years.includes('2020') ? data['2020'].toFixed(2) : '-'}</td></tr>
                    <tr><td>2005</td><td>${years.includes('2005') ? data['2005'].toFixed(2) : '-'}</td>
                        <td>2015</td><td>${years.includes('2015') ? data['2015'].toFixed(2) : '-'}</td>
                        <td>2024</td><td>${years.includes('2024') ? data['2024'].toFixed(2) : '-'}</td></tr>
                </table>
                <div class="stats">
                    <div><span>📊 Изменение 2000→2024</span>
                        <strong class="${change >= 0 ? 'positive' : 'negative'}">${change >= 0 ? '+' : ''}${change.toFixed(2)}${info.unit} (${changePercent}%)</strong>
                    </div>
                </div>
            `;
            dashboard.appendChild(card);
            
            const plotData = [{
                x: years,
                y: values,
                type: 'scatter',
                mode: 'lines+markers',
                name: pair,
                line: { color: info.color, width: 3 },
                marker: { size: 10, color: info.color },
                fill: 'tozeroy',
                fillcolor: `rgba(${parseInt(info.color.slice(1,3),16)}, ${parseInt(info.color.slice(3,5),16)}, ${parseInt(info.color.slice(5,7),16)}, 0.2)`
            }];
            const layout = {
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#fff' },
                margin: { t: 10, r: 10, b: 40, l: 60 },
                xaxis: { title: 'Год', gridcolor: 'rgba(255,255,255,0.1)' },
                yaxis: { title: `Курс к USD${info.unit}`, gridcolor: 'rgba(255,255,255,0.1)' }
            };
            Plotly.newPlot(`chart-hist-${pair.replace(/[ /()]/g, '-')}`, plotData, layout, { responsive: true, displaylogo: false });
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Главная страница с текущими курсами"""
    return render_template_string(MAIN_PAGE_TEMPLATE)

@app.route('/historical')
def historical():
    """Страница с историческими данными"""
    return render_template_string(HISTORICAL_PAGE_TEMPLATE, historical_data=historical_rates)

@app.route('/api/prices')
def get_prices():
    """API для получения текущих курсов"""
    try:
        pairs_data = {}
        for pair, history in price_history.items():
            if history:
                prices = [h['price'] for h in history]
                current_price = prices[-1]
                min_price = min(prices)
                max_price = max(prices)
                change = current_price - prices[0]
                pairs_data[pair] = {
                    'current': current_price,
                    'min': min_price,
                    'max': max_price,
                    'change': change,
                    'history': history,
                    'volatility': ((max_price - min_price) / current_price * 100) if current_price else 0
                }
        return jsonify({'pairs': pairs_data, 'last_update': datetime.now().strftime('%H:%M:%S'), 'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'})

@app.route('/api/historical')
def get_historical():
    """API для получения исторических данных"""
    return jsonify({'historical': historical_rates, 'status': 'success'})

@app.route('/robots.txt')
def robots_txt():
    content = """User-agent: *
Allow: /
Sitemap: https://ваш-домен.ru/sitemap.xml
Crawl-delay: 10
"""
    return make_response(content, 200, {'Content-Type': 'text/plain'})

@app.route('/sitemap.xml')
def sitemap():
    sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{request.url_root}</loc>
    <lastmod>{datetime.now().date().isoformat()}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{request.url_root}historical</loc>
    <lastmod>{datetime.now().date().isoformat()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>'''
    return make_response(sitemap_xml, 200, {'Content-Type': 'application/xml'})

if __name__ == '__main__':
    if not any(price_history.values()):
        initialize_with_backup_data()
    thread = threading.Thread(target=update_prices, daemon=True)
    thread.start()
    print("🚀 Сервер запущен на http://localhost:5000")
    print("📊 Главная страница: http://localhost:5000/")
    print("📈 Исторические данные: http://localhost:5000/historical")
    print("💵 Валюты: EUR, GBP, JPY, CNY, AUD, CAD, CHF")
    print("🥇 Металлы: Gold, Silver, Copper, Aluminum, Tin")
    print("📅 Исторические данные: 2000, 2005, 2010, 2015, 2020, 2024")
    app.run(debug=True, port=5000, use_reloader=False)