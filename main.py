import asyncio
import logging
import os
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton, 
    CallbackQuery, Message
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy import BigInteger, String, Float, ForeignKey, Text, DateTime, select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# --- CONFIG ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///db.sqlite3")

# --- DB MODELS ---
class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    referrer_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    orders: Mapped[list['Order']] = relationship(back_populates='user')

class Category(Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    products: Mapped[list['Product']] = relationship(back_populates='category')

class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    content: Mapped[str] = mapped_column(Text)
    category: Mapped['Category'] = relationship(back_populates='products')

class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped['User'] = relationship(back_populates='orders')

# --- ENGINE ---
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# --- STATES ---
class AdminStates(StatesGroup):
    add_cat_name = State()
    add_prod_name = State()
    add_prod_desc = State()
    add_prod_price = State()
    add_prod_content = State()
    broadcast_msg = State()

# --- MIDDLEWARE ---
class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)

# --- DYNAMIC KEYBOARDS ---
def main_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="👤 Личный кабинет")],
        [KeyboardButton(text="💰 Пополнение"), KeyboardButton(text="💸 Вывод")],
        [KeyboardButton(text="📋 Информация")]
    ]
    # ЕСЛИ ПОЛЬЗОВАТЕЛЬ АДМИН — ДОБАВЛЯЕМ КНОПКУ АДМИНКИ
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="👨‍💻 Админка")])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Категория"), KeyboardButton(text="➕ Товар")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📢 Рассылка")],
        [KeyboardButton(text="🏠 Меню")]
    ], resize_keyboard=True)

def back_btn(callback_data: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data))
    return builder.as_markup()

# --- HANDLERS ---
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    res = await session.execute(select(User).where(User.id == message.from_user.id))
    user = res.scalar_one_or_none()
    
    if not user:
        user = User(id=message.from_user.id, username=message.from_user.username, referrer_id=ref_id)
        session.add(user)
        await session.commit()
        if ref_id and ref_id != user.id:
            res_ref = await session.execute(select(User).where(User.id == ref_id))
            ref_user = res_ref.scalar_one_or_none()
            if ref_user:
                ref_user.balance += 10.0
                await session.commit()

    await message.answer(f"🔥 **Shadow Store**\n\nДобро пожаловать!", 
                         reply_markup=main_menu_kb(message.from_user.id), parse_mode="Markdown")

# --- ADMIN COMMANDS ---
@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def cmd_admin_enter(message: Message):
    await message.answer("👨‍💻 **Панель управления:**", reply_markup=admin_menu_kb(), parse_mode="Markdown")

@dp.message(F.text == "👨‍💻 Админка", F.from_user.id == ADMIN_ID)
async def admin_panel_click(message: Message):
    await message.answer("👨‍💻 **Панель управления:**", reply_markup=admin_menu_kb(), parse_mode="Markdown")

# --- SHOP HANDLERS ---
@dp.message(F.text == "🛒 Магазин")
async def shop_main(message: Message, session: AsyncSession):
    res = await session.execute(select(Category))
    cats = res.scalars().all()
    builder = InlineKeyboardBuilder()
    for c in cats:
        builder.add(InlineKeyboardButton(text=f"📁 {c.name}", callback_data=f"cat_{c.id}"))
    builder.adjust(2)
    await message.answer("📂 **Выберите категорию:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("cat_"))
async def cat_products(callback: CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split("_")[1])
    res = await session.execute(select(Product).where(Product.category_id == cat_id))
    prods = res.scalars().all()
    builder = InlineKeyboardBuilder()
    for p in prods:
        builder.add(InlineKeyboardButton(text=f"{p.name} — ${p.price}", callback_data=f"p_{p.id}"))
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_cats"))
    builder.adjust(1)
    await callback.message.edit_text("📦 **Товары:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_cats")
async def back_cats(callback: CallbackQuery, session: AsyncSession):
    await shop_main(callback.message, session)

@dp.callback_query(F.data.startswith("p_"))
async def prod_view(callback: CallbackQuery, session: AsyncSession):
    pid = int(callback.data.split("_")[1])
    res = await session.execute(select(Product).where(Product.id == pid))
    p = res.scalar_one_or_none()
    if not p: return
    text = f"💎 **{p.name}**\n\n📝 {p.description}\n\n💰 **Цена: ${p.price}**"
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🛒 Купить", callback_data=f"buy_{p.id}"))
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cat_{p.category_id}"))
    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_item(callback: CallbackQuery, session: AsyncSession):
    pid = int(callback.data.split("_")[1])
    uid = callback.from_user.id
    res_p = await session.execute(select(Product).where(Product.id == pid))
    p = res_p.scalar_one_or_none()
    res_u = await session.execute(select(User).where(User.id == uid))
    u = res_u.scalar_one_or_none()
    if u.balance < p.price:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    u.balance -= p.price
    session.add(Order(user_id=u.id, product_id=p.id, price=p.price))
    await session.commit()
    await callback.message.answer(f"✅ **Куплено!**\n\n📦 Контент:\n`{p.content}`", parse_mode="Markdown")
    await callback.answer()

# --- USER MENU ---
@dp.message(F.text == "👤 Личный кабинет")
async def profile(message: Message, session: AsyncSession):
    res = await session.execute(select(User).where(User.id == message.from_user.id))
    u = res.scalar_one_or_none()
    ref_link = f"https://t.me/{(await message.bot.get_me()).username}?start={u.id}"
    text = (f"👤 **Профиль**\n\n"
            f"🆔 ID: `{u.id}`\n"
            f"💰 Баланс: **${u.balance:.2f}**\n"
            f"🔗 Реф: `{ref_link}`")
    await message.answer(text, reply_markup=main_menu_kb(u.id), parse_mode="Markdown")

@dp.message(F.text == "💰 Пополнение")
async def deposit(message: Message):
    await message.answer("💳 **Пополнение**\n\nПишите: @ManerProga", parse_mode="Markdown")

@dp.message(F.text == "💸 Вывод")
async def withdraw(message: Message):
    await message.answer("📤 **Вывод**\n\nПишите: @ManerProga", parse_mode="Markdown")

@dp.message(F.text == "📋 Информация")
async def info(message: Message):
    await message.answer("ℹ️ **Shadow Store v1.0**\nПоддержка: @ManerProga", parse_mode="Markdown")

# --- ADMIN ACTIONS ---
@dp.message(F.text == "🏠 Меню", F.from_user.id == ADMIN_ID)
async def admin_home(message: Message):
    await message.answer("👨‍💻 **Панель управления:**", reply_markup=admin_menu_kb(), parse_mode="Markdown")

@dp.message(F.text == "➕ Категория", F.from_user.id == ADMIN_ID)
async def adm_cat(message: Message, state: FSMContext):
    await message.answer("Введите имя категории:")
    await state.set_state(AdminStates.add_cat_name)

@dp.message(AdminStates.add_cat_name)
async def adm_cat_save(message: Message, state: FSMContext, session: AsyncSession):
    session.add(Category(name=message.text))
    await session.commit()
    await message.answer("✅ Создано!")
    await state.clear()

@dp.message(F.text == "➕ Товар", F.from_user.id == ADMIN_ID)
async def adm_prod(message: Message, state: FSMContext):
    await message.answer("Название товара:")
    await state.set_state(AdminStates.add_prod_name)

@dp.message(AdminStates.add_prod_name)
async def adm_p_name(message: Message, state: FSMContext):
    await state.update_data(n=message.text)
    await message.answer("Описание:")
    await state.set_state(AdminStates.add_prod_desc)

@dp.message(AdminStates.add_prod_desc)
async def adm_p_desc(message: Message, state: FSMContext):
    await state.update_data(d=message.text)
    await message.answer("Цена (число):")
    await state.set_state(AdminStates.add_prod_price)

@dp.message(AdminStates.add_prod_price)
async def adm_p_price(message: Message, state: FSMContext):
    try:
        await state.update_data(p=float(message.text))
        await message.answer("Контент (ссылка/текст):")
        await state.set_state(AdminStates.add_prod_content)
    except: await message.answer("Ошибка! Введите число.")

@dp.message(AdminStates.add_prod_content)
async def adm_p_final(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    res = await session.execute(select(Category))
    cat = res.scalars().first()
    if not cat: return await message.answer("Нет категорий!")
    session.add(Product(category_id=cat.id, name=data['n'], description=data['d'], price=data['p'], content=message.text))
    await session.commit()
    await message.answer("✅ Товар добавлен!")
    await state.clear()

@dp.message(F.text == "📊 Статистика", F.from_user.id == ADMIN_ID)
async def adm_stat(message: Message, session: AsyncSession):
    u_count = await session.execute(select(func.count(User.id)))
    o_count = await session.execute(select(func.count(Order.id)))
    rev = await session.execute(select(func.sum(Order.price)))
    await message.answer(f"📊 **Статистика**\n\nЮзеров: `{u_count.scalar()}`\nЗаказов: `{o_count.scalar()}`\nВыручка: `${rev.scalar() or 0:.2f}`", parse_mode="Markdown")

@dp.message(F.text == "📢 Рассылка", F.from_user.id == ADMIN_ID)
async def adm_broad(message: Message, state: FSMContext):
    await message.answer("Введите текст рассылки:")
    await state.set_state(AdminStates.broadcast_msg)

@dp.message(AdminStates.broadcast_msg)
async def adm_broad_run(message: Message, state: FSMContext, session: AsyncSession):
    res = await session.execute(select(User.id))
    ids = res.scalars().all()
    count = 0
    for uid in ids:
        try:
            await message.bot.send_message(uid, message.text, parse_mode="Markdown")
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await message.answer(f"✅ Рассылка: {count} чел.")
    await state.clear()

# --- INIT ---
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        res = await session.execute(select(Category))
        if not res.scalars().first():
            c = Category(name="Общее")
            session.add(c)
            await session.commit()
            await session.execute(select(c))
            session.add(Product(category_id=c.id, name="Test", description="Test", price=1.0, content="TEST"))
            await session.commit()

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
