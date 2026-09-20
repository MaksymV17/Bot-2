import telebot
import requests
import os
import time
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import threading

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Перемінна для збереження правильного chat_id
user_chat_id = 698035711
amount_in_uah = 0  # Змінна для збереження введеної суми

# Словник відповідності назв монет їх ID в CoinGecko
# Словник відповідності назв монет їх ID в CoinGecko
COIN_IDS = {
    "bitcoin": "bitcoin",
    "ethereum": "ethereum",
    "tether": "tether",  # Додай цей рядок
    "binancecoin": "binancecoin",
    "solana": "solana",
    "ton": "the-open-network",
    "the-open-network": "the-open-network"
}

# Назви монет для відображення
COIN_NAMES = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "tether": "USDT",  # Додай цей рядок
    "binancecoin": "BNB",
    "solana": "Solana",
    "the-open-network": "TON"
}

# Створюємо закріплену клавіатуру (шапка з кнопками)
def create_fixed_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [
        KeyboardButton("📊 Топ 5 криптовалют"),
        KeyboardButton("🧮 Калькулятор"),
        KeyboardButton("🔍 Пошук монети")
    ]
    keyboard.add(*buttons)
    return keyboard

# Отримуємо курс криптовалюти в гривнях
def get_exchange_rate(currency):
    """Отримуємо курс криптовалюти в гривнях з API CoinGecko."""
    try:
        coin_id = COIN_IDS.get(currency, currency)
        
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "uah,usd"
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        if coin_id in data:
            return data[coin_id]
        else:
            # Спробуємо альтернативні ID для TON
            if currency == "ton":
                for alt_id in ["the-open-network", "toncoin"]:
                    params["ids"] = alt_id
                    response = requests.get(url, params=params)
                    data = response.json()
                    if alt_id in data:
                        return data[alt_id]
            return None
    except Exception as e:
        print(f"Помилка отримання курсу: {e}")
        return None

# Отримуємо топ криптовалют
def get_top_crypto(limit=5):
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": False
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        result = "📊 Топ криптовалют:\n\n"
        for coin in data:
            # Замінюємо XRP на TON
            if coin['symbol'].upper() == "XRP":
                coin_name = "TON"
                coin_symbol = "TON"
            else:
                coin_name = coin['name']
                coin_symbol = coin['symbol'].upper()
            
            result += f"{coin_name} ({coin_symbol})\n"
            result += f"💰 Ціна: {coin['current_price']:,.2f} USD\n"
            
            change = coin['price_change_percentage_24h']
            if change is not None:
                result += f"📈 24h: {change:.5f}%\n\n"
            else:
                result += f"📈 24h: 0.00000%\n\n"
        
        return result
    except Exception as e:
        print(f"Помилка отримання топ криптовалют: {e}")
        return "❌ Помилка отримання даних. Спробуйте пізніше."

# Отримуємо інформацію про конкретну монету
def get_coin_info(coin_id):
    try:
        actual_id = COIN_IDS.get(coin_id, coin_id)
        
        url = f"https://api.coingecko.com/api/v3/coins/{actual_id}"
        params = {
            "localization": False,
            "tickers": False,
            "market_data": True,
            "community_data": False,
            "developer_data": False
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        result = f"📌 {data['name']} ({data['symbol'].upper()})\n\n"
        result += f"💰 Ціна: {data['market_data']['current_price']['usd']:,.2f} USD\n"
        result += f"🇺🇦 В гривні: {data['market_data']['current_price']['uah']:,.2f} грн\n"
        result += f"📊 Капіталізація: {data['market_data']['market_cap']['usd']:,.0f} USD\n"
        result += f"📈 24h: {data['market_data']['price_change_percentage_24h']:.5f}%\n"
        result += f"🔗 Детальніше: {data['links']['homepage'][0]}"
        
        return result
    except Exception as e:
        print(f"Помилка отримання інформації: {e}")
        return "❌ Монету не знайдено!"

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
        bot.send_message(message.chat.id, "🔎 Введіть назву монети (наприклад: bitcoin, ethereum, dogecoin, ton):")
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
            "❌ Будь ласка, введіть коректне число!\n"
            "Наприклад: 1000 або 500.50"
        )

@bot.callback_query_handler(func=lambda call: True)
def select_crypto(call):
    global amount_in_uah
    
    try:
        selected_currency = call.data
        
        if amount_in_uah <= 0:
            bot.send_message(call.message.chat.id, "❌ Спочатку введіть суму в гривнях!")
            return

        # Отримуємо курс
        rates = get_exchange_rate(selected_currency)
        
        if not rates:
            bot.send_message(call.message.chat.id, "❌ Не вдалося отримати курс. Спробуйте пізніше.")
            return
            
        rate_uah = rates['uah']
        rate_usd = rates['usd']
        
        result = amount_in_uah / rate_uah
        
        # Назва монети
        coin_name = COIN_NAMES.get(selected_currency, selected_currency.capitalize())
        if selected_currency == "ton":
            coin_name = "TON"
        elif selected_currency == "binancecoin":
            coin_name = "BNB"
        
        # Форматуємо результат
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
        print(f"Помилка: {e}")
        bot.send_message(
            call.message.chat.id, 
            "❌ Сталася помилка при розрахунку. Спробуйте ще раз."
        )

# Функція для автооновлення
def auto_update():
    while True:
        if user_chat_id:
            try:
                data = get_top_crypto(5)
                if not data.startswith("❌"):
                    bot.send_message(user_chat_id, f"🔄 {data}")
            except Exception as e:
                print(f"Помилка автооновлення: {e}")
        time.sleep(43200)

# Запускаємо автооновлення в окремому потоці
threading.Thread(target=auto_update, daemon=True).start()

print("✅ Бот запущено...")
 
bot.infinity_polling()