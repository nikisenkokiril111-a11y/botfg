import asyncio
import logging
import os
import random
import string
import time
from datetime import datetime, date, timedelta

import aiosqlite
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    LabeledPrice, Message, PreCheckoutQuery, ReplyKeyboardMarkup,
    KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]
DB_PATH = "cases_bot.db"

CASES = [
    {
        "id": 1, "name": "🎁 Стартовый кейс", "price": 15,
        "items": [
            {"name": "Монета ⭐", "stars": 5, "weight": 50},
            {"name": "Малый бонус ⭐", "stars": 10, "weight": 30},
            {"name": "Средний бонус ⭐", "stars": 20, "weight": 15},
            {"name": "Большой бонус ⭐", "stars": 50, "weight": 4},
            {"name": "Джекпот ⭐", "stars": 150, "weight": 1},
        ]
    },
    {
        "id": 2, "name": "💎 Алмазный кейс", "price": 50,
        "items": [
            {"name": "Кристалл ⭐", "stars": 20, "weight": 40},
            {"name": "Алмаз ⭐", "stars": 50, "weight": 30},
            {"name": "Изумруд ⭐", "stars": 100, "weight": 20},
            {"name": "Сапфир ⭐", "stars": 200, "weight": 8},
            {"name": "Алмазный джекпот ⭐", "stars": 500, "weight": 2},
        ]
    },
    {
        "id": 3, "name": "🔥 Огненный кейс", "price": 75,
        "items": [
            {"name": "Искра ⭐", "stars": 30, "weight": 40},
            {"name": "Пламя ⭐", "stars": 75, "weight": 30},
            {"name": "Инферно ⭐", "stars": 150, "weight": 18},
            {"name": "Феникс ⭐", "stars": 300, "weight": 10},
            {"name": "Дракон ⭐", "stars": 750, "weight": 2},
        ]
    },
    {
        "id": 4, "name": "🌊 Морской кейс", "price": 100,
        "items": [
            {"name": "Ракушка ⭐", "stars": 40, "weight": 40},
            {"name": "Жемчуг ⭐", "stars": 100, "weight": 28},
            {"name": "Коралл ⭐", "stars": 200, "weight": 18},
            {"name": "Трезубец ⭐", "stars": 400, "weight": 12},
            {"name": "Посейдон ⭐", "stars": 1000, "weight": 2},
        ]
    },
    {
        "id": 5, "name": "⚡ Молниеносный кейс", "price": 150,
        "items": [
            {"name": "Разряд ⭐", "stars": 60, "weight": 40},
            {"name": "Гром ⭐", "stars": 150, "weight": 28},
            {"name": "Молния ⭐", "stars": 300, "weight": 18},
            {"name": "Шторм ⭐", "stars": 600, "weight": 12},
            {"name": "Зевс ⭐", "stars": 1500, "weight": 2},
        ]
    },
    {
        "id": 6, "name": "🏆 Чемпионский кейс", "price": 200,
        "items": [
            {"name": "Медаль ⭐", "stars": 80, "weight": 40},
            {"name": "Серебро ⭐", "stars": 200, "weight": 28},
            {"name": "Золото ⭐", "stars": 400, "weight": 18},
            {"name": "Платина ⭐", "stars": 800, "weight": 12},
            {"name": "Гран-при ⭐", "stars": 2000, "weight": 2},
        ]
    },
    {
        "id": 7, "name": "🌙 Лунный кейс", "price": 300,
        "items": [
            {"name": "Лунный свет ⭐", "stars": 120, "weight": 40},
            {"name": "Звезда ⭐", "stars": 300, "weight": 28},
            {"name": "Созвездие ⭐", "stars": 600, "weight": 18},
            {"name": "Галактика ⭐", "stars": 1200, "weight": 12},
            {"name": "Вселенная ⭐", "stars": 3000, "weight": 2},
        ]
    },
    {
        "id": 8, "name": "🎰 Казино кейс", "price": 400,
        "items": [
            {"name": "7️⃣ Семёрка ⭐", "stars": 160, "weight": 35},
            {"name": "🍒 Вишня ⭐", "stars": 400, "weight": 28},
            {"name": "💰 Монеты ⭐", "stars": 800, "weight": 22},
            {"name": "💎 Бриллиант ⭐", "stars": 1600, "weight": 13},
            {"name": "🎰 Джекпот ⭐", "stars": 4000, "weight": 2},
        ]
    },
    {
        "id": 9, "name": "🦁 Дикий кейс", "price": 500,
        "items": [
            {"name": "Лапа ⭐", "stars": 200, "weight": 40},
            {"name": "Коготь ⭐", "stars": 500, "weight": 28},
            {"name": "Клык ⭐", "stars": 1000, "weight": 18},
            {"name": "Грива ⭐", "stars": 2000, "weight": 12},
            {"name": "Лев 👑 ⭐", "stars": 5000, "weight": 2},
        ]
    },
    {
        "id": 10, "name": "🚀 Космический кейс", "price": 750,
        "items": [
            {"name": "Астероид ⭐", "stars": 300, "weight": 40},
            {"name": "Комета ⭐", "stars": 750, "weight": 28},
            {"name": "Планета ⭐", "stars": 1500, "weight": 18},
            {"name": "Звездолёт ⭐", "stars": 3000, "weight": 12},
            {"name": "Чёрная дыра ⭐", "stars": 7500, "weight": 2},
        ]
    },
    {
        "id": 11, "name": "🧊 Ледяной кейс", "price": 1000,
        "items": [
            {"name": "Снежинка ⭐", "stars": 400, "weight": 40},
            {"name": "Лёд ⭐", "stars": 1000, "weight": 28},
            {"name": "Метель ⭐", "stars": 2000, "weight": 18},
            {"name": "Вьюга ⭐", "stars": 4000, "weight": 12},
            {"name": "Абсолютный ноль ⭐", "stars": 10000, "weight": 2},
        ]
    },
    {
        "id": 12, "name": "☠️ Пиратский кейс", "price": 1500,
        "items": [
            {"name": "Монета пирата ⭐", "stars": 600, "weight": 40},
            {"name": "Сундук ⭐", "stars": 1500, "weight": 28},
            {"name": "Карта ⭐", "stars": 3000, "weight": 18},
            {"name": "Ром ⭐", "stars": 6000, "weight": 12},
            {"name": "Чёрная метка ⭐", "stars": 15000, "weight": 2},
        ]
    },
    {
        "id": 13, "name": "👑 Королевский кейс", "price": 2000,
        "items": [
            {"name": "Скипетр ⭐", "stars": 800, "weight": 40},
            {"name": "Корона ⭐", "stars": 2000, "weight": 28},
            {"name": "Трон ⭐", "stars": 4000, "weight": 18},
            {"name": "Дворец ⭐", "stars": 8000, "weight": 12},
            {"name": "Империя ⭐", "stars": 20000, "weight": 2},
        ]
    },
    {
        "id": 14, "name": "🌈 Радужный кейс", "price": 3000,
        "items": [
            {"name": "Цвет радуги ⭐", "stars": 1200, "weight": 40},
            {"name": "Дуга ⭐", "stars": 3000, "weight": 28},
            {"name": "Горшок с золотом ⭐", "stars": 6000, "weight": 18},
            {"name": "Единорог ⭐", "stars": 12000, "weight": 12},
            {"name": "Радужный дракон ⭐", "stars": 30000, "weight": 2},
        ]
    },
    {
        "id": 15, "name": "💥 МЕГАКЕЙС", "price": 5000,
        "items": [
            {"name": "Мега-шанс ⭐", "stars": 2000, "weight": 40},
            {"name": "Мега-приз ⭐", "stars": 5000, "weight": 28},
            {"name": "Суперприз ⭐", "stars": 10000, "weight": 18},
            {"name": "Ультраприз ⭐", "stars": 20000, "weight": 12},
            {"name": "🔥 АБСОЛЮТНЫЙ ДЖЕКПОТ 🔥 ⭐", "stars": 50000, "weight": 2},
        ]
    },
]

DAILY_CASE = {
    "id": 0, "name": "🎀 Ежедневный кейс", "price": 0,
    "items": [
        {"name": "Утешительный приз ⭐", "stars": 1, "weight": 50},
        {"name": "Маленький подарок ⭐", "stars": 3, "weight": 30},
        {"name": "Хороший подарок ⭐", "stars": 7, "weight": 15},
        {"name": "Отличный подарок ⭐", "stars": 15, "weight": 4},
        {"name": "Суперприз дня ⭐", "stars": 50, "weight": 1},
    ]
}

SELL_MULTIPLIER = 0.5


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                stars INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                daily_last TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_name TEXT,
                stars_value INTEGER,
                case_id INTEGER,
                obtained_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS withdrawal_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                item_name TEXT,
                stars_value INTEGER,
                inventory_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                type TEXT,
                value REAL,
                max_uses INTEGER DEFAULT 1,
                uses INTEGER DEFAULT 0,
                expires_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_uses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                code TEXT,
                used_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS case_overrides (
                case_id INTEGER PRIMARY KEY,
                price INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                stars INTEGER,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_user(db, user_id):
    async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
        return await cur.fetchone()


async def ensure_user(db, user_id, username=None, first_name=None):
    user = await get_user(db, user_id)
    if not user:
        await db.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()
        user = await get_user(db, user_id)
    return user


async def add_stars(db, user_id, amount, description=""):
    await db.execute("UPDATE users SET stars = stars + ? WHERE user_id=?", (amount, user_id))
    await db.execute(
        "INSERT INTO transactions (user_id, type, stars, description) VALUES (?,?,?,?)",
        (user_id, "credit" if amount >= 0 else "debit", abs(amount), description)
    )
    await db.commit()


def get_case_by_id(case_id):
    if case_id == 0:
        return DAILY_CASE
    for c in CASES:
        if c["id"] == case_id:
            return c
    return None


def roll_item(items):
    weights = [item["weight"] for item in items]
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for item in items:
        cumulative += item["weight"]
        if r <= cumulative:
            return item
    return items[-1]


def apply_chance_bonus(items, bonus_percent):
    if bonus_percent <= 0:
        return items
    modified = []
    for item in items:
        new_weight = item["weight"] * (1 + bonus_percent / 100)
        modified.append({**item, "weight": new_weight})
    return modified


def main_menu_keyboard(is_admin=False):
    kb = [
        [KeyboardButton(text="🎁 Магазин кейсов"), KeyboardButton(text="📦 Мой инвентарь")],
        [KeyboardButton(text="🎰 Казино"), KeyboardButton(text="🎀 Ежедневный кейс")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🎫 Промокод")],
        [KeyboardButton(text="📤 Вывод предмета")],
    ]
    if is_admin:
        kb.append([KeyboardButton(text="⚙️ Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def is_admin(user_id):
    return user_id in ADMIN_IDS


router = Router()


class BotStates(StatesGroup):
    entering_promo = State()
    casino_rocket_bet = State()
    casino_coin_bet = State()
    admin_give_stars_id = State()
    admin_give_stars_amount = State()
    admin_ban_id = State()
    admin_unban_id = State()
    admin_user_info_id = State()
    admin_edit_case_price = State()
    admin_create_promo_type = State()
    admin_create_promo_code = State()
    admin_create_promo_value = State()
    admin_create_promo_max_uses = State()
    admin_create_promo_expires = State()
    withdrawal_select_item = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, message.from_user.id,
                          message.from_user.username,
                          message.from_user.first_name)
    admin = is_admin(message.from_user.id)
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "Добро пожаловать в <b>CaseMaster</b> — лучший симулятор открытия кейсов!\n\n"
        "⭐ Здесь ты можешь:\n"
        "• Открывать крутые кейсы за Telegram Stars\n"
        "• Играть в казино (Ракета и Орёл/Решка)\n"
        "• Получать ежедневный бесплатный кейс\n"
        "• Выводить выигранные предметы\n\n"
        "Выбери действие ниже 👇",
        reply_markup=main_menu_keyboard(admin),
        parse_mode=ParseMode.HTML
    )


@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        user = await ensure_user(db, message.from_user.id,
                                 message.from_user.username,
                                 message.from_user.first_name)
        async with db.execute("SELECT COUNT(*) FROM inventory WHERE user_id=?", (message.from_user.id,)) as cur:
            inv_count = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM withdrawal_requests WHERE user_id=? AND status='pending'", (message.from_user.id,)) as cur:
            pending = (await cur.fetchone())[0]

    uid, uname, fname, stars, banned, daily_last, created = user
    uname_display = f"@{uname}" if uname else "нет"
    daily_info = "Доступен сейчас!" if not daily_last or daily_last != str(date.today()) else "Уже получен сегодня"
    banned_info = " ⛔ ЗАБАНЕН" if banned else ""

    await message.answer(
        f"👤 <b>Профиль{banned_info}</b>\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"👤 Username: {uname_display}\n"
        f"⭐ Баланс: <b>{stars} Stars</b>\n"
        f"📦 Предметов в инвентаре: {inv_count}\n"
        f"📤 Заявок на вывод: {pending}\n"
        f"🎀 Ежедневный кейс: {daily_info}\n"
        f"📅 Регистрация: {created[:10] if created else '—'}",
        parse_mode=ParseMode.HTML
    )


@router.message(F.text == "🎁 Магазин кейсов")
async def shop_handler(message: Message):
    builder = InlineKeyboardBuilder()
    for case in CASES:
        builder.button(text=f"{case['name']} — {case['price']} ⭐", callback_data=f"case_info:{case['id']}")
    builder.adjust(1)
    await message.answer(
        "🎁 <b>Магазин кейсов</b>\n\nВыбери кейс, который хочешь открыть:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data.startswith("case_info:"))
async def case_info_callback(callback: CallbackQuery):
    case_id = int(callback.data.split(":")[1])
    case = get_case_by_id(case_id)
    if not case:
        await callback.answer("Кейс не найден", show_alert=True)
        return

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT price FROM case_overrides WHERE case_id=?", (case_id,)) as cur:
            override = await cur.fetchone()
    price = override[0] if override else case["price"]

    total_weight = sum(i["weight"] for i in case["items"])
    items_text = ""
    for item in case["items"]:
        chance = round(item["weight"] / total_weight * 100, 1)
        items_text += f"  • {item['name']} ({item['stars']} ⭐) — {chance}%\n"

    builder = InlineKeyboardBuilder()
    builder.button(text=f"🎰 Открыть за {price} ⭐", callback_data=f"buy_case:{case_id}")
    builder.button(text="◀️ Назад", callback_data="back_to_shop")
    builder.adjust(1)

    await callback.message.edit_text(
        f"<b>{case['name']}</b>\n\n"
        f"💰 Цена: {price} ⭐\n\n"
        f"🎁 Содержимое:\n{items_text}",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_shop")
async def back_to_shop(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for case in CASES:
        builder.button(text=f"{case['name']} — {case['price']} ⭐", callback_data=f"case_info:{case['id']}")
    builder.adjust(1)
    await callback.message.edit_text(
        "🎁 <b>Магазин кейсов</b>\n\nВыбери кейс, который хочешь открыть:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_case:"))
async def buy_case_callback(callback: CallbackQuery):
    case_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        user = await ensure_user(db, user_id)
        if user[4]:
            await callback.answer("⛔ Вы заблокированы", show_alert=True)
            return

        async with db.execute("SELECT price FROM case_overrides WHERE case_id=?", (case_id,)) as cur:
            override = await cur.fetchone()

    case = get_case_by_id(case_id)
    price = override[0] if override else case["price"]

    if user[3] >= price:
        async with aiosqlite.connect(DB_PATH) as db:
            bonus = await get_user_active_chance_bonus(db, user_id)
            items = apply_chance_bonus(case["items"], bonus)
            item = roll_item(items)
            await add_stars(db, user_id, -price, f"Открытие кейса #{case_id}")
            await db.execute(
                "INSERT INTO inventory (user_id, item_name, stars_value, case_id) VALUES (?,?,?,?)",
                (user_id, item["name"], item["stars"], case_id)
            )
            await db.commit()

        builder = InlineKeyboardBuilder()
        builder.button(text="🎰 Открыть ещё раз", callback_data=f"buy_case:{case_id}")
        builder.button(text="◀️ В магазин", callback_data="back_to_shop")
        builder.adjust(1)

        await callback.message.edit_text(
            f"🎉 <b>Кейс открыт!</b>\n\n"
            f"Ты получил: <b>{item['name']}</b>\n"
            f"Стоимость: {item['stars']} ⭐\n\n"
            f"💰 Твой баланс: {user[3] - price} ⭐",
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
    else:
        await send_stars_invoice(callback, case, price)
    await callback.answer()


async def send_stars_invoice(callback: CallbackQuery, case: dict, price: int):
    await callback.message.answer_invoice(
        title=case["name"],
        description=f"Открытие кейса {case['name']}",
        payload=f"case:{case['id']}",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=price)],
    )


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    stars_paid = message.successful_payment.total_amount

    if payload.startswith("case:"):
        case_id = int(payload.split(":")[1])
        case = get_case_by_id(case_id)
        async with aiosqlite.connect(DB_PATH) as db:
            await ensure_user(db, user_id, message.from_user.username, message.from_user.first_name)
            bonus = await get_user_active_chance_bonus(db, user_id)
            items = apply_chance_bonus(case["items"], bonus)
            item = roll_item(items)
            await db.execute(
                "INSERT INTO inventory (user_id, item_name, stars_value, case_id) VALUES (?,?,?,?)",
                (user_id, item["name"], item["stars"], case_id)
            )
            await add_stars(db, user_id, stars_paid, f"Пополнение через Stars за кейс #{case_id}")
            await add_stars(db, user_id, -stars_paid, f"Открытие кейса #{case_id}")
            await db.commit()
            user = await get_user(db, user_id)

        await message.answer(
            f"🎉 <b>Оплата прошла! Кейс открыт!</b>\n\n"
            f"Ты получил: <b>{item['name']}</b>\n"
            f"Стоимость предмета: {item['stars']} ⭐\n\n"
            f"💰 Баланс: {user[3]} ⭐",
            parse_mode=ParseMode.HTML
        )
    elif payload.startswith("topup:"):
        amount = int(payload.split(":")[1])
        async with aiosqlite.connect(DB_PATH) as db:
            await ensure_user(db, user_id, message.from_user.username, message.from_user.first_name)
            await add_stars(db, user_id, amount, "Пополнение баланса")
            user = await get_user(db, user_id)
        await message.answer(
            f"✅ Баланс пополнен на {amount} ⭐\n\n"
            f"💰 Текущий баланс: {user[3]} ⭐",
            parse_mode=ParseMode.HTML
        )


@router.message(F.text == "🎀 Ежедневный кейс")
async def daily_case_handler(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        user = await ensure_user(db, user_id, message.from_user.username, message.from_user.first_name)
        if user[4]:
            await message.answer("⛔ Вы заблокированы")
            return

        today = str(date.today())
        if user[5] == today:
            await message.answer(
                "⏳ Ежедневный кейс уже получен!\n\n"
                "Возвращайся завтра 🌅",
                parse_mode=ParseMode.HTML
            )
            return

        case = DAILY_CASE
        bonus = await get_user_active_chance_bonus(db, user_id)
        items = apply_chance_bonus(case["items"], bonus)
        item = roll_item(items)

        await db.execute("UPDATE users SET daily_last=? WHERE user_id=?", (today, user_id))
        await db.execute(
            "INSERT INTO inventory (user_id, item_name, stars_value, case_id) VALUES (?,?,?,?)",
            (user_id, item["name"], item["stars"], 0)
        )
        await db.commit()
        user = await get_user(db, user_id)

    await message.answer(
        f"🎀 <b>Ежедневный кейс открыт!</b>\n\n"
        f"Ты получил: <b>{item['name']}</b>\n"
        f"Стоимость: {item['stars']} ⭐\n\n"
        f"💰 Баланс: {user[3]} ⭐\n\n"
        f"Приходи завтра за новым кейсом! 🌅",
        parse_mode=ParseMode.HTML
    )


@router.message(F.text == "📦 Мой инвентарь")
async def inventory_handler(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, item_name, stars_value, obtained_at FROM inventory WHERE user_id=? ORDER BY obtained_at DESC LIMIT 20",
            (user_id,)
        ) as cur:
            items = await cur.fetchall()

    if not items:
        await message.answer("📦 Ваш инвентарь пуст.\n\nОткрывайте кейсы, чтобы получить предметы!")
        return

    builder = InlineKeyboardBuilder()
    for item in items:
        sell_price = int(item[2] * SELL_MULTIPLIER)
        builder.button(
            text=f"{item[1]} ({sell_price} ⭐)",
            callback_data=f"sell_item:{item[0]}:{sell_price}"
        )
    builder.adjust(1)
    builder.button(text="📤 Вывести предмет", callback_data="withdraw_menu")

    text = "📦 <b>Ваш инвентарь</b> (последние 20 предметов):\n\n"
    for item in items:
        sell_price = int(item[2] * SELL_MULTIPLIER)
        text += f"• {item[1]} — продать за {sell_price} ⭐\n"
    text += "\n<i>Нажмите на предмет, чтобы продать его боту</i>"

    await message.answer(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("sell_item:"))
async def sell_item_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    item_id = int(parts[1])
    sell_price = int(parts[2])
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM inventory WHERE id=? AND user_id=?", (item_id, user_id)) as cur:
            item = await cur.fetchone()
        if not item:
            await callback.answer("❌ Предмет не найден", show_alert=True)
            return
        await db.execute("DELETE FROM inventory WHERE id=?", (item_id,))
        await add_stars(db, user_id, sell_price, f"Продажа предмета: {item[2]}")
        user = await get_user(db, user_id)

    await callback.answer(f"✅ Продан за {sell_price} ⭐!", show_alert=True)
    await callback.message.edit_text(
        f"✅ <b>Продано!</b>\n\n"
        f"Предмет: {item[2]}\n"
        f"Получено: {sell_price} ⭐\n\n"
        f"💰 Баланс: {user[3]} ⭐",
        parse_mode=ParseMode.HTML
    )


@router.message(F.text == "📤 Вывод предмета")
async def withdrawal_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        user = await ensure_user(db, user_id)
        if user[4]:
            await message.answer("⛔ Вы заблокированы")
            return
        async with db.execute(
            "SELECT id, item_name, stars_value FROM inventory WHERE user_id=? ORDER BY stars_value DESC LIMIT 20",
            (user_id,)
        ) as cur:
            items = await cur.fetchall()

    if not items:
        await message.answer("📦 Ваш инвентарь пуст. Нечего выводить!")
        return

    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(text=f"{item[1]} ({item[2]} ⭐)", callback_data=f"withdraw_item:{item[0]}")
    builder.adjust(1)

    await message.answer(
        "📤 <b>Вывод предмета</b>\n\nВыберите предмет для вывода:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data.startswith("withdraw_item:"))
async def withdraw_item_callback(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM inventory WHERE id=? AND user_id=?", (item_id, user_id)) as cur:
            item = await cur.fetchone()
        if not item:
            await callback.answer("❌ Предмет не найден", show_alert=True)
            return
        user = await get_user(db, user_id)
        username = user[1] or f"id{user_id}"

        async with db.execute("SELECT COUNT(*) FROM withdrawal_requests WHERE inventory_id=?", (item_id,)) as cur:
            existing = (await cur.fetchone())[0]
        if existing:
            await callback.answer("⚠️ Заявка уже подана!", show_alert=True)
            return

        await db.execute(
            "INSERT INTO withdrawal_requests (user_id, username, item_name, stars_value, inventory_id) VALUES (?,?,?,?,?)",
            (user_id, username, item[2], item[3], item_id)
        )
        await db.commit()

    await callback.answer("✅ Заявка на вывод подана!", show_alert=True)
    await callback.message.edit_text(
        f"📤 <b>Заявка подана!</b>\n\n"
        f"Предмет: {item[2]}\n"
        f"Стоимость: {item[3]} ⭐\n\n"
        f"Администратор рассмотрит вашу заявку в ближайшее время.",
        parse_mode=ParseMode.HTML
    )


@router.message(F.text == "🎫 Промокод")
async def promo_handler(message: Message, state: FSMContext):
    await state.set_state(BotStates.entering_promo)
    await message.answer(
        "🎫 <b>Активация промокода</b>\n\nВведите ваш промокод:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )


@router.message(BotStates.entering_promo)
async def promo_enter_handler(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    user_id = message.from_user.id
    await state.clear()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM promo_codes WHERE code=?", (code,)) as cur:
            promo = await cur.fetchone()

        if not promo:
            await message.answer(
                "❌ Промокод не найден!",
                reply_markup=main_menu_keyboard(is_admin(user_id))
            )
            return

        pid, pcode, ptype, pvalue, max_uses, uses, expires_at, created = promo

        if uses >= max_uses:
            await message.answer(
                "❌ Промокод уже использован максимальное количество раз!",
                reply_markup=main_menu_keyboard(is_admin(user_id))
            )
            return

        if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
            await message.answer(
                "❌ Срок действия промокода истёк!",
                reply_markup=main_menu_keyboard(is_admin(user_id))
            )
            return

        async with db.execute("SELECT COUNT(*) FROM promo_uses WHERE user_id=? AND code=?", (user_id, code)) as cur:
            already_used = (await cur.fetchone())[0]

        if already_used:
            await message.answer(
                "❌ Вы уже использовали этот промокод!",
                reply_markup=main_menu_keyboard(is_admin(user_id))
            )
            return

        await db.execute("UPDATE promo_codes SET uses=uses+1 WHERE code=?", (code,))
        await db.execute("INSERT INTO promo_uses (user_id, code) VALUES (?,?)", (user_id, code))

        if ptype == "stars":
            await add_stars(db, user_id, int(pvalue), f"Промокод {code}")
            msg = f"✅ Промокод активирован!\n\nПолучено: {int(pvalue)} ⭐"
        elif ptype == "chance":
            await db.execute(
                "INSERT INTO transactions (user_id, type, stars, description) VALUES (?,?,?,?)",
                (user_id, "chance_bonus", int(pvalue), f"Промокод {code} - бонус шанса {pvalue}% на 24ч")
            )
            msg = f"✅ Промокод активирован!\n\nБонус шанса: +{pvalue}% на 24 часа"
        elif ptype == "discount":
            await db.execute(
                "INSERT INTO transactions (user_id, type, stars, description) VALUES (?,?,?,?)",
                (user_id, "discount", int(pvalue), f"Промокод {code} - скидка {pvalue}%")
            )
            msg = f"✅ Промокод активирован!\n\nСкидка {pvalue}% на следующую покупку"
        else:
            msg = "✅ Промокод активирован!"

        await db.commit()

    await message.answer(msg, reply_markup=main_menu_keyboard(is_admin(user_id)), parse_mode=ParseMode.HTML)


async def get_user_active_chance_bonus(db, user_id):
    async with db.execute(
        "SELECT stars, description FROM transactions WHERE user_id=? AND type='chance_bonus' ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    ) as cur:
        row = await cur.fetchone()
    if not row:
        return 0
    async with db.execute(
        "SELECT created_at FROM transactions WHERE user_id=? AND type='chance_bonus' ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    ) as cur:
        ts_row = await cur.fetchone()
    if ts_row:
        from datetime import timezone
        try:
            created_at = datetime.fromisoformat(ts_row[0])
            if datetime.now() - created_at < timedelta(hours=24):
                return row[0]
        except Exception:
            pass
    return 0


@router.message(F.text == "🎰 Казино")
async def casino_handler(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Ракета (Crash)", callback_data="casino:rocket")
    builder.button(text="🪙 Орёл / Решка", callback_data="casino:coin")
    builder.adjust(1)
    await message.answer(
        "🎰 <b>Казино</b>\n\nВыберите игру:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "casino:rocket")
async def casino_rocket_info(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.casino_rocket_bet)
    await callback.message.answer(
        "🚀 <b>Ракета (Crash)</b>\n\n"
        "Ставишь звёзды. Ракета взлетает, множитель растёт.\n"
        "Ты выбираешь когда забрать деньги, пока ракета не взорвалась!\n"
        "Если ракета взрывается до твоего решения — теряешь всё.\n\n"
        "Введите размер ставки (в звёздах):",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.message(BotStates.casino_rocket_bet)
async def casino_rocket_bet_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        bet = int(message.text.strip())
        if bet <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Введите корректное число звёзд (больше 0)")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(db, user_id)
        if not user or user[4]:
            await state.clear()
            await message.answer("⛔ Доступ ограничен", reply_markup=main_menu_keyboard(is_admin(user_id)))
            return
        if user[3] < bet:
            await message.answer(f"❌ Недостаточно звёзд! У вас: {user[3]} ⭐")
            return

    await state.update_data(bet=bet)

    crash_at = round(random.uniform(1.0, 10.0), 2)
    multipliers = [1.2, 1.5, 2.0, 3.0, 5.0, 10.0]

    builder = InlineKeyboardBuilder()
    for m in multipliers:
        if m < crash_at:
            builder.button(text=f"✅ Забрать при x{m}", callback_data=f"rocket_cashout:{m}:{crash_at}:{bet}")
        else:
            builder.button(text=f"💥 x{m}", callback_data=f"rocket_crash:{m}:{crash_at}:{bet}")
    builder.adjust(2)

    await state.clear()
    await message.answer(
        f"🚀 <b>Ракета летит!</b>\n\n"
        f"Ставка: {bet} ⭐\n"
        f"Выберите когда забрать деньги:\n"
        f"<i>(Некоторые точки могут оказаться после взрыва!)</i>",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data.startswith("rocket_cashout:"))
async def rocket_cashout_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    chosen_mult = float(parts[1])
    crash_at = float(parts[2])
    bet = int(parts[3])
    user_id = callback.from_user.id

    if chosen_mult < crash_at:
        winnings = int(bet * chosen_mult)
        async with aiosqlite.connect(DB_PATH) as db:
            await add_stars(db, user_id, winnings - bet, f"Казино Ракета x{chosen_mult}")
            user = await get_user(db, user_id)
        await callback.message.edit_text(
            f"🚀 <b>Ракета!</b>\n\n"
            f"✅ Вы забрали при x{chosen_mult}!\n"
            f"Ракета взорвалась бы при x{crash_at}\n\n"
            f"Ставка: {bet} ⭐\n"
            f"Выигрыш: {winnings} ⭐ (+{winnings - bet} ⭐)\n\n"
            f"💰 Баланс: {user[3]} ⭐",
            parse_mode=ParseMode.HTML
        )
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await add_stars(db, user_id, -bet, f"Казино Ракета - проигрыш")
            user = await get_user(db, user_id)
        await callback.message.edit_text(
            f"🚀 <b>Ракета!</b>\n\n"
            f"💥 Ракета взорвалась при x{crash_at}!\n"
            f"Вы выбрали слишком поздно (x{chosen_mult})\n\n"
            f"Потеряно: {bet} ⭐\n\n"
            f"💰 Баланс: {user[3]} ⭐",
            parse_mode=ParseMode.HTML
        )
    await callback.answer()


@router.callback_query(F.data.startswith("rocket_crash:"))
async def rocket_crash_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    crash_at = float(parts[2])
    bet = int(parts[3])
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        await add_stars(db, user_id, -bet, f"Казино Ракета - взрыв")
        user = await get_user(db, user_id)

    await callback.message.edit_text(
        f"🚀 <b>Ракета!</b>\n\n"
        f"💥 ВЗРЫВ! Ракета взорвалась до x{crash_at}\n\n"
        f"Потеряно: {bet} ⭐\n\n"
        f"💰 Баланс: {user[3]} ⭐",
        parse_mode=ParseMode.HTML
    )
    await callback.answer("💥 Взрыв!", show_alert=True)


@router.callback_query(F.data == "casino:coin")
async def casino_coin_info(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.casino_coin_bet)
    await callback.message.answer(
        "🪙 <b>Орёл / Решка</b>\n\n"
        "Угадай результат броска монеты!\n"
        "Правильный ответ = x2 к ставке.\n\n"
        "Введите размер ставки (в звёздах):",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.message(BotStates.casino_coin_bet)
async def casino_coin_bet_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        bet = int(message.text.strip())
        if bet <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Введите корректное число звёзд (больше 0)")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(db, user_id)
        if not user or user[4]:
            await state.clear()
            await message.answer("⛔ Доступ ограничен", reply_markup=main_menu_keyboard(is_admin(user_id)))
            return
        if user[3] < bet:
            await message.answer(f"❌ Недостаточно звёзд! У вас: {user[3]} ⭐")
            return

    await state.update_data(bet=bet)
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.button(text="🦅 Орёл", callback_data=f"coin:heads:{bet}")
    builder.button(text="🪙 Решка", callback_data=f"coin:tails:{bet}")
    builder.adjust(2)

    await message.answer(
        f"🪙 <b>Орёл или Решка?</b>\n\nСтавка: {bet} ⭐\n\nВыбирайте:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data.startswith("coin:"))
async def coin_flip_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    choice = parts[1]
    bet = int(parts[2])
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(db, user_id)
        if user[3] < bet:
            await callback.answer("❌ Недостаточно звёзд!", show_alert=True)
            return

        bonus = await get_user_active_chance_bonus(db, user_id)
        heads_weight = 50 + bonus / 2
        tails_weight = 50 - bonus / 2
        result = random.choices(["heads", "tails"], weights=[heads_weight, tails_weight])[0]

        won = (result == choice)
        if won:
            await add_stars(db, user_id, bet, f"Казино Монета - победа")
            emoji = "🦅" if result == "heads" else "🪙"
            text = f"🪙 <b>Орёл / Решка</b>\n\n{emoji} Выпало: {'Орёл' if result == 'heads' else 'Решка'}\n\n✅ Вы угадали!\nВыигрыш: +{bet} ⭐"
        else:
            await add_stars(db, user_id, -bet, f"Казино Монета - проигрыш")
            emoji = "🦅" if result == "heads" else "🪙"
            text = f"🪙 <b>Орёл / Решка</b>\n\n{emoji} Выпало: {'Орёл' if result == 'heads' else 'Решка'}\n\n❌ Не угадали!\nПотеряно: {bet} ⭐"

        user = await get_user(db, user_id)
        text += f"\n\n💰 Баланс: {user[3]} ⭐"

    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Сыграть ещё", callback_data="casino:coin")
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()


@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Пользователи", callback_data="admin:users")
    builder.button(text="🎁 Управление кейсами", callback_data="admin:cases")
    builder.button(text="📤 Заявки на вывод", callback_data="admin:withdrawals")
    builder.button(text="🎫 Промокоды", callback_data="admin:promos")
    builder.button(text="📊 Статистика", callback_data="admin:stats")
    builder.adjust(1)
    await message.answer("⚙️ <b>Админ-панель</b>", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "admin:stats")
async def admin_stats_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned=1") as cur:
            banned = (await cur.fetchone())[0]
        async with db.execute("SELECT SUM(stars) FROM users") as cur:
            total_stars = (await cur.fetchone())[0] or 0
        async with db.execute("SELECT COUNT(*) FROM inventory") as cur:
            total_items = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM withdrawal_requests WHERE status='pending'") as cur:
            pending_wr = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM promo_codes") as cur:
            total_promos = (await cur.fetchone())[0]

    await callback.message.edit_text(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"⛔ Забанено: {banned}\n"
        f"⭐ Всего звёзд у юзеров: {total_stars}\n"
        f"📦 Предметов в инвентарях: {total_items}\n"
        f"📤 Заявок на вывод: {pending_wr}\n"
        f"🎫 Промокодов: {total_promos}",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "admin:users")
async def admin_users_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Найти пользователя по ID", callback_data="admin:user_info")
    builder.button(text="⭐ Выдать звёзды", callback_data="admin:give_stars")
    builder.button(text="⛔ Забанить", callback_data="admin:ban")
    builder.button(text="✅ Разбанить", callback_data="admin:unban")
    builder.button(text="◀️ Назад", callback_data="admin:back")
    builder.adjust(1)
    await callback.message.edit_text("👥 <b>Управление пользователями</b>", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data == "admin:back")
async def admin_back_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Пользователи", callback_data="admin:users")
    builder.button(text="🎁 Управление кейсами", callback_data="admin:cases")
    builder.button(text="📤 Заявки на вывод", callback_data="admin:withdrawals")
    builder.button(text="🎫 Промокоды", callback_data="admin:promos")
    builder.button(text="📊 Статистика", callback_data="admin:stats")
    builder.adjust(1)
    await callback.message.edit_text("⚙️ <b>Админ-панель</b>", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data == "admin:user_info")
async def admin_user_info_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    await state.set_state(BotStates.admin_user_info_id)
    await callback.message.answer("🔍 Введите ID пользователя:")
    await callback.answer()


@router.message(BotStates.admin_user_info_id)
async def admin_user_info_id_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректный ID")
        await state.clear()
        return
    await state.clear()
    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(db, target_id)
        if not user:
            await message.answer("❌ Пользователь не найден")
            return
        async with db.execute("SELECT COUNT(*) FROM inventory WHERE user_id=?", (target_id,)) as cur:
            inv_count = (await cur.fetchone())[0]

    uid, uname, fname, stars, banned, daily_last, created = user
    await message.answer(
        f"👤 <b>Пользователь</b>\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"👤 Username: @{uname or '—'}\n"
        f"📝 Имя: {fname or '—'}\n"
        f"⭐ Баланс: {stars}\n"
        f"📦 Инвентарь: {inv_count} предметов\n"
        f"⛔ Бан: {'Да' if banned else 'Нет'}\n"
        f"📅 Регистрация: {created[:10] if created else '—'}",
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "admin:give_stars")
async def admin_give_stars_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    await state.set_state(BotStates.admin_give_stars_id)
    await callback.message.answer("⭐ Введите ID пользователя:")
    await callback.answer()


@router.message(BotStates.admin_give_stars_id)
async def admin_give_stars_id_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректный ID")
        await state.clear()
        return
    await state.update_data(target_id=target_id)
    await state.set_state(BotStates.admin_give_stars_amount)
    await message.answer("⭐ Введите количество звёзд:")


@router.message(BotStates.admin_give_stars_amount)
async def admin_give_stars_amount_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректное количество")
        await state.clear()
        return
    data = await state.get_data()
    target_id = data["target_id"]
    await state.clear()

    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(db, target_id)
        if not user:
            await message.answer("❌ Пользователь не найден")
            return
        await add_stars(db, target_id, amount, f"Выдано администратором")
        user = await get_user(db, target_id)

    await message.answer(
        f"✅ Выдано {amount} ⭐ пользователю <code>{target_id}</code>\n"
        f"Новый баланс: {user[3]} ⭐",
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "admin:ban")
async def admin_ban_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    await state.set_state(BotStates.admin_ban_id)
    await callback.message.answer("⛔ Введите ID пользователя для бана:")
    await callback.answer()


@router.message(BotStates.admin_ban_id)
async def admin_ban_id_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректный ID")
        await state.clear()
        return
    await state.clear()
    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(db, target_id)
        if not user:
            await message.answer("❌ Пользователь не найден")
            return
        await db.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (target_id,))
        await db.commit()
    await message.answer(f"⛔ Пользователь <code>{target_id}</code> забанен", parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "admin:unban")
async def admin_unban_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    await state.set_state(BotStates.admin_unban_id)
    await callback.message.answer("✅ Введите ID пользователя для разбана:")
    await callback.answer()


@router.message(BotStates.admin_unban_id)
async def admin_unban_id_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректный ID")
        await state.clear()
        return
    await state.clear()
    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(db, target_id)
        if not user:
            await message.answer("❌ Пользователь не найден")
            return
        await db.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (target_id,))
        await db.commit()
    await message.answer(f"✅ Пользователь <code>{target_id}</code> разбанен", parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "admin:cases")
async def admin_cases_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for case in CASES:
        builder.button(text=case["name"], callback_data=f"admin_case_edit:{case['id']}")
    builder.button(text="◀️ Назад", callback_data="admin:back")
    builder.adjust(1)
    await callback.message.edit_text("🎁 <b>Управление кейсами</b>\n\nВыберите кейс:", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_case_edit:"))
async def admin_case_edit_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    case_id = int(callback.data.split(":")[1])
    case = get_case_by_id(case_id)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT price FROM case_overrides WHERE case_id=?", (case_id,)) as cur:
            override = await cur.fetchone()
    current_price = override[0] if override else case["price"]
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить цену", callback_data=f"admin_case_price:{case_id}")
    builder.button(text="◀️ Назад", callback_data="admin:cases")
    builder.adjust(1)
    await callback.message.edit_text(
        f"🎁 <b>{case['name']}</b>\n\n"
        f"Текущая цена: {current_price} ⭐\n"
        f"Базовая цена: {case['price']} ⭐",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_case_price:"))
async def admin_case_price_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    case_id = int(callback.data.split(":")[1])
    await state.update_data(edit_case_id=case_id)
    await state.set_state(BotStates.admin_edit_case_price)
    await callback.message.answer("✏️ Введите новую цену кейса (в звёздах):")
    await callback.answer()


@router.message(BotStates.admin_edit_case_price)
async def admin_edit_case_price_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        new_price = int(message.text.strip())
        if new_price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Некорректная цена")
        await state.clear()
        return
    data = await state.get_data()
    case_id = data["edit_case_id"]
    await state.clear()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO case_overrides (case_id, price) VALUES (?,?)",
            (case_id, new_price)
        )
        await db.commit()
    case = get_case_by_id(case_id)
    await message.answer(f"✅ Цена кейса <b>{case['name']}</b> изменена на {new_price} ⭐", parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "admin:withdrawals")
async def admin_withdrawals_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, username, item_name, stars_value, created_at FROM withdrawal_requests WHERE status='pending' ORDER BY created_at ASC LIMIT 10",
        ) as cur:
            requests = await cur.fetchall()

    if not requests:
        await callback.message.edit_text(
            "📤 <b>Заявки на вывод</b>\n\nПустых заявок нет.",
            reply_markup=InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="admin:back").as_markup(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        return

    for req in requests:
        req_id, username, item_name, stars_value, created_at = req
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Одобрить", callback_data=f"wr_approve:{req_id}")
        builder.button(text="❌ Отклонить", callback_data=f"wr_reject:{req_id}")
        builder.adjust(2)
        await callback.message.answer(
            f"📤 <b>Заявка #{req_id}</b>\n\n"
            f"👤 Пользователь: @{username}\n"
            f"📦 Предмет: {item_name}\n"
            f"⭐ Стоимость: {stars_value}\n"
            f"📅 Дата: {created_at[:16]}",
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
    await callback.answer()


@router.callback_query(F.data.startswith("wr_approve:"))
async def wr_approve_callback(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    req_id = int(callback.data.split(":")[1])
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM withdrawal_requests WHERE id=?", (req_id,)) as cur:
            req = await cur.fetchone()
        if not req:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        if req[6] != "pending":
            await callback.answer("⚠️ Заявка уже обработана", show_alert=True)
            return
        await db.execute("UPDATE withdrawal_requests SET status='approved' WHERE id=?", (req_id,))
        await db.execute("DELETE FROM inventory WHERE id=?", (req[5],))
        await db.commit()

    try:
        await bot.send_message(
            req[1],
            f"✅ <b>Ваша заявка на вывод одобрена!</b>\n\n"
            f"Предмет: {req[3]}\n"
            f"Стоимость: {req[4]} ⭐\n\n"
            f"С вами свяжутся для передачи предмета.",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    await callback.message.edit_text(
        f"✅ Заявка #{req_id} одобрена!\n\nПредмет: {req[3]}\nПользователь: @{req[2]}",
        parse_mode=ParseMode.HTML
    )
    await callback.answer("✅ Одобрено!")


@router.callback_query(F.data.startswith("wr_reject:"))
async def wr_reject_callback(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    req_id = int(callback.data.split(":")[1])
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM withdrawal_requests WHERE id=?", (req_id,)) as cur:
            req = await cur.fetchone()
        if not req:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        if req[6] != "pending":
            await callback.answer("⚠️ Заявка уже обработана", show_alert=True)
            return
        await db.execute("UPDATE withdrawal_requests SET status='rejected' WHERE id=?", (req_id,))
        await db.commit()

    try:
        await bot.send_message(
            req[1],
            f"❌ <b>Ваша заявка на вывод отклонена.</b>\n\n"
            f"Предмет: {req[3]}\n\n"
            f"Предмет возвращён в инвентарь. Обратитесь к администратору за подробностями.",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    await callback.message.edit_text(
        f"❌ Заявка #{req_id} отклонена!\n\nПредмет: {req[3]}\nПользователь: @{req[2]}",
        parse_mode=ParseMode.HTML
    )
    await callback.answer("❌ Отклонено!")


@router.callback_query(F.data == "admin:promos")
async def admin_promos_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Создать промокод", callback_data="admin_create_promo")
    builder.button(text="📋 Список промокодов", callback_data="admin_list_promos")
    builder.button(text="◀️ Назад", callback_data="admin:back")
    builder.adjust(1)
    await callback.message.edit_text("🎫 <b>Управление промокодами</b>", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data == "admin_list_promos")
async def admin_list_promos_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT code, type, value, uses, max_uses, expires_at FROM promo_codes ORDER BY created_at DESC LIMIT 15") as cur:
            promos = await cur.fetchall()

    if not promos:
        await callback.message.edit_text(
            "🎫 Промокодов нет.",
            reply_markup=InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="admin:promos").as_markup()
        )
        await callback.answer()
        return

    text = "🎫 <b>Промокоды:</b>\n\n"
    for p in promos:
        code, ptype, value, uses, max_uses, expires = p
        type_names = {"stars": "⭐ Звёзды", "chance": "🎯 Шанс", "discount": "💰 Скидка"}
        type_name = type_names.get(ptype, ptype)
        text += f"• <code>{code}</code> — {type_name} {value} | {uses}/{max_uses}\n"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="admin:promos").as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "admin_create_promo")
async def admin_create_promo_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    await state.set_state(BotStates.admin_create_promo_type)
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Звёзды (stars)", callback_data="promo_type:stars")
    builder.button(text="🎯 Бонус шанса (chance)", callback_data="promo_type:chance")
    builder.button(text="💰 Скидка (discount)", callback_data="promo_type:discount")
    builder.adjust(1)
    await callback.message.answer("🎫 Выберите тип промокода:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("promo_type:"), BotStates.admin_create_promo_type)
async def promo_type_selected(callback: CallbackQuery, state: FSMContext):
    ptype = callback.data.split(":")[1]
    await state.update_data(promo_type=ptype)
    await state.set_state(BotStates.admin_create_promo_code)
    type_hints = {
        "stars": "⭐ Сколько звёзд выдать?\nВведите число:",
        "chance": "🎯 Процент бонуса к шансу?\nВведите число (например, 20 для +20%):",
        "discount": "💰 Процент скидки?\nВведите число (например, 10 для -10%):"
    }
    await callback.message.answer(type_hints.get(ptype, "Введите значение:"))
    await state.set_state(BotStates.admin_create_promo_value)
    await callback.answer()


@router.message(BotStates.admin_create_promo_value)
async def admin_promo_value_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        value = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректное значение")
        await state.clear()
        return
    await state.update_data(promo_value=value)
    await state.set_state(BotStates.admin_create_promo_max_uses)
    await message.answer("🔢 Максимальное количество использований (введите число):")


@router.message(BotStates.admin_create_promo_max_uses)
async def admin_promo_max_uses_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        max_uses = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректное число")
        await state.clear()
        return
    await state.update_data(promo_max_uses=max_uses)
    await state.set_state(BotStates.admin_create_promo_code)
    await message.answer("✏️ Введите код промокода (или отправьте 'авто' для автогенерации):")


@router.message(BotStates.admin_create_promo_code)
async def admin_promo_code_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    code_input = message.text.strip().upper()
    if code_input == "АВТО" or code_input == "АВТО":
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    else:
        code = code_input

    data = await state.get_data()
    await state.clear()

    promo_type = data.get("promo_type", "stars")
    promo_value = data.get("promo_value", 0)
    max_uses = data.get("promo_max_uses", 1)

    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO promo_codes (code, type, value, max_uses) VALUES (?,?,?,?)",
                (code, promo_type, promo_value, max_uses)
            )
            await db.commit()
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
            return

    type_names = {"stars": "⭐ Звёзды", "chance": "🎯 Шанс", "discount": "💰 Скидка"}
    await message.answer(
        f"✅ <b>Промокод создан!</b>\n\n"
        f"Код: <code>{code}</code>\n"
        f"Тип: {type_names.get(promo_type, promo_type)}\n"
        f"Значение: {promo_value}\n"
        f"Макс. использований: {max_uses}",
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "withdraw_menu")
async def withdraw_menu_callback(callback: CallbackQuery):
    await callback.answer("Используйте кнопку '📤 Вывод предмета' в главном меню", show_alert=True)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан! Установите переменную окружения BOT_TOKEN")
        return

    await init_db()

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    logger.info("Бот запускается...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "pre_checkout_query"])


if __name__ == "__main__":
    asyncio.run(main())
