import os
import time
import threading
import requests
from flask import Flask
import telebot
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# 1. Запуск фонового веб-сервера Flask для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# 2. Инициализация бота и переменных
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

user_chat_id = None
amount_in_uah = 0

# Заголовки для предотвращения блокировки со стороны API
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Карта соответствия названий монет тикерам
SYMBOL_MAP = {
    "bitcoin": "BTC",
    "btc": "BTC",
    "ethereum": "ETH",
    "eth": "ETH",
    "tether": "USDT",
    "usdt": "USDT",
    "binancecoin": "BNB",
    "bnb": "BNB",
    "solana": "SOL",
    "sol": "SOL",
    "ton": "TON",
    "the-open-network": "TON",
    "toncoin": "TON"
}

COIN_NAMES = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "tether": "USDT",
    "binancecoin": "BNB",
    "solana": "Solana",
    "ton": "TON"
}

def get_symbol(currency):
    curr_clean = str(currency).lower().strip()
    return SYMBOL_MAP.get(curr_clean, curr_clean.upper())

# Клавиатура меню
def create_fixed_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [
        KeyboardButton("📊 Топ 5 криптовалют"),
        KeyboardButton("🧮 Калькулятор"),
        KeyboardButton("🔍 Пошук монети")
    ]
    keyboard.add(*buttons)
    return keyboard

# 3. Функции работы с API (CryptoCompare)

def get_exchange_rate(currency):
    """Получение курса конкретной монеты в UAH и USD"""
    symbol = get_symbol(currency)
    try:
        url = f"https://min-api.cryptocompare.com/data/pricemulti?fsyms={symbol}&tsyms=USD,UAH"
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        
        if symbol in data:
            return {
                'uah': data[symbol].get('UAH', 0),
                'usd': data[symbol].get('USD', 0)
            }
        return None
    except Exception as e:
        print(f"Помилка отримання курсу: {e}")
        return None

def get_top_crypto(limit=5):
    """Получение топ-5 криптовалют по капитализации"""
    try:
        url = f"https://min-api.cryptocompare.com/data/top/mktcapfull?limit={limit}&tsym=USD"
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        
        if "Data" not in data:
            return "❌ Помилка отримання даних."

        result = "📊 Топ криптовалют:\n\n"
        for item in data["Data"]:
            info = item.get("CoinInfo", {})
            raw = item.get("RAW", {}).get("USD", {})
            
            name = info.get("FullName", "Unknown")
            symbol = info.get("Name", "")
            price = raw.get("PRICE", 0)
            change = raw.get("CHANGEPCT24HOUR", 0)

            result += f"🔹 {name} ({symbol})\n"
            result += f"💰 Ціна: ${price:,.2f} USD\n"
            result += f"📈 24h: {change:.2f}%\n\n"
        
        return result
    except Exception as e:
        print(f"Помилка отримання топ криптовалют: {e}")
        return "❌ Помилка отримання даних. Спробуйте пізніше."

def get_coin_info(coin_id):
    """Поиск детальной информации по монете"""
    symbol = get_symbol(coin_id)
    try:
        url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={symbol}&tsyms=USD,UAH"
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        
        if "RAW" in data and symbol in data["RAW"]:
            raw_usd = data["RAW"][symbol]["USD"]
            raw_uah = data["RAW"][symbol]["UAH"]
            
            price_usd = raw_usd.get("PRICE", 0)
            price_uah = raw_uah.get("PRICE", 0)
            mcap = raw_usd.get("MKTCAP", 0)
            change = raw_usd.get("CHANGEPCT24HOUR", 0)
            
            result = f"📌 {symbol}\n\n"
            result += f"💰 Ціна: ${price_usd:,.2f} USD\n"
            result += f"🇺🇦 В гривні: {price_uah:,.2f} грн\n"
            result += f"📊 Капіталізація: ${mcap:,.0f} USD\n"
            result += f"📈 24h: {change:.2f}%\n"
            return result
        else:
            return "❌ Монету не знайдено!"
    except Exception as e:
        print(f"Помилка отримання інформації: {e}")
        return "❌ Монету не знайдено!"

# 4. Хэндлеры команд и сообщений Telegram

@bot.message_handler(commands=['start'])
def start(message):
    global user_chat_id
    user_chat_id = message.chat.id
    
    welcome_text = (
        "🚀 Вітаю в Crypto Rynok Bot!\n\n"
        "Я ваш персональний помічник у світі криптовалюти.\n"
        "Тут ви можете відстежувати курси, конвертувати валюту та знаходити інформацію про криптоактиви.\n\n"
        "📊 Мої можливості:\n"
        "• Топ-5 найбільших криптовалют\n"
        "• Конвертація гривні в крипту\n"
        "• Детальний пошук монет\n\n"
        "👇 Обирайте функцію з меню нижче!"
    )
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_fixed_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.text == "📊 Топ 5 криптовалют":
        crypto_data = get_top_crypto(limit=5)
        bot.send_message(message.chat.id, crypto_data)
    
    elif message.text == "🔍 Пошук монети":
        bot.send_message(message.chat.id, "🔎 Введіть назву або тикер монети (наприклад: btc, eth, doge, ton, sol):")
        bot.register_next_step_handler(message, search_coin_by_symbol)
    
    elif message.text == "🧮 Калькулятор":
        bot.send_message(message.chat.id, "💰 Введіть суму в гривнях для конвертації:")
        bot.register_next_step_handler(message, ask_crypto)

def search_coin_by_symbol(message):
    coin_id = message.text.lower().strip()
    coin_info = get_coin_info(coin_id)
    bot.send_message(message.chat.id, coin_info, disable_web_page_preview=True)

def ask_crypto(message):
    global amount_in_uah
    try:
        amount_in_uah = float(message.text.replace(',', '.'))

        keyboard = InlineKeyboardMarkup(row_width=3)
        button_btc = InlineKeyboardButton("Bitcoin", callback_data="bitcoin")
        button_eth = InlineKeyboardButton("Ethereum", callback_data="ethereum")
        button_usdt = InlineKeyboardButton("USDT", callback_data="tether")
        button_bnb = InlineKeyboardButton("BNB", callback_data="binancecoin")
        button_sol = InlineKeyboardButton("Solana", callback_data="solana")
        button_ton = InlineKeyboardButton("TON", callback_data="ton")
        
        keyboard.add(button_btc, button_eth, button_usdt)
        keyboard.add(button_bnb, button_sol, button_ton)
        
        bot.send_message(
            message.chat.id,
            f"💵 Ви ввели: {amount_in_uah:,.2f} грн\n\n"
            f"🪙 Оберіть криптовалюту для конвертації:",
            reply_markup=keyboard
        )

    except ValueError:
        bot.send_message(
            message.chat.id, 
            "❌ Будь ласка, введіть коректне число!\nНаприклад: 1000 або 500.50"
        )

@bot.callback_query_handler(func=lambda call: True)
def select_crypto(call):
    global amount_in_uah
    
    try:
        selected_currency = call.data
        
        if amount_in_uah <= 0:
            bot.send_message(call.message.chat.id, "❌ Спочатку введіть суму в гривнях!")
            return

        rates = get_exchange_rate(selected_currency)
        
        if not rates or rates['uah'] == 0:
            bot.send_message(call.message.chat.id, "❌ Не вдалося отримати курс. Спробуйте пізніше.")
            return
            
        rate_uah = rates['uah']
        rate_usd = rates['usd']
        
        result = amount_in_uah / rate_uah
        coin_name = COIN_NAMES.get(selected_currency, selected_currency.upper())
        
        if result < 0.01:
            result_str = f"{result:.8f}"
        elif result < 1:
            result_str = f"{result:.6f}"
        else:
            result_str = f"{result:.4f}"
        
        bot.send_message(
            call.message.chat.id,
            f"✅ Результат конвертації:\n\n"
            f"💵 {amount_in_uah:,.2f} грн = {result_str} {coin_name}\n\n"
            f"📊 Курс: 1 {coin_name} = {rate_uah:,.2f} грн | ${rate_usd:,.2f} USD"
        )
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
    except Exception as e:
        print(f"Помилка конвертації: {e}")
        bot.send_message(
            call.message.chat.id, 
            "❌ Сталася помилка при розрахунку. Спробуйте ще раз."
        )

# 5. Точка входа
if __name__ == "__main__":
    print("✅ Бот успішно запущено і слухає повідомлення...")
    try:
        bot.remove_webhook()
    except Exception:
        pass
    bot.infinity_polling(skip_pending=True)