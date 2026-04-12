import asyncio
import logging
import os
from datetime import datetime
from typing import Any

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

# --- ENGINE & SESSION ---
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# --- STATES ---
class AdminStates(StatesGroup):
    add_cat_name = State()
    add_prod_name = State()
    add_prod_desc = State()
    add_prod_price = State()
    add_prod_content = State()

# --- MIDDLEWARE ---
class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)

# --- KEYBOARDS ---
def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Магазин")],
        [KeyboardButton(text="💰 Пополнение"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="📋 Инфо")]
    ], resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Категория"), KeyboardButton(text="➕ Товар")],
        [KeyboardButton(text="📊 Статистика")]
    ], resize_keyboard=True)

# --- HANDLERS ---
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def start(message: Message, session: AsyncSession):
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
                ref_user.balance += 5.0
                await session.commit()

    await message.answer(f"👋 Привет, {message.from_user.first_name}!", reply_markup=main_kb())

@dp.message(F.text == "🛒 Магазин")
async def shop(message: Message, session: AsyncSession):
    res = await session.execute(select(Category))
    cats = res.scalars().all()
    builder = InlineKeyboardBuilder()
    for c in cats:
        builder.add(InlineKeyboardButton(text=c.name, callback_data=f"cat_{c.id}"))
    builder.adjust(2)
    await message.answer("📂 Выберите категорию:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cat_"))
async def show_prods(callback: CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split("_")[1])
    res = await session.execute(select(Product).where(Product.category_id == cat_id))
    prods = res.scalars().all()
    builder = InlineKeyboardBuilder()
    for p in prods:
        builder.add(InlineKeyboardButton(text=f"{p.name} (${p.price})", callback_data=f"p_{p.id}"))
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_cats"))
    builder.adjust(1)
    await callback.message.edit_text("📦 Товары:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "back_to_cats")
async def back_cats(callback: CallbackQuery, session: AsyncSession):
    await shop(callback.message, session)

@dp.callback_query(F.data.startswith("p_"))
async def prod_info(callback: CallbackQuery, session: AsyncSession):
    pid = int(callback.data.split("_")[1])
    res = await session.execute(select(Product).where(Product.id == pid))
    p = res.scalar_one_or_none()
    if not p: return
    
    text = f"💎 **{p.name}**\n\n{p.description}\n\n💰 Цена: ${p.price}"
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🛒 Купить", callback_data=f"buy_{p.id}"))
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cat_{p.category_id}"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def buy(callback: CallbackQuery, session: AsyncSession):
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
    await callback.message.answer(f"✅ Успешно!\n\n📦 Контент:\n`{p.content}`", parse_mode="Markdown")
    await callback.answer()

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message, session: AsyncSession):
    res = await session.execute(select(User).where(User.id == message.from_user.id))
    u = res.scalar_one_or_none()
    await message.answer(f"👤 **Профиль**\n\n💰 Баланс: `${u.balance:.2f}`\n🆔 ID: `{u.id}`", parse_mode="Markdown")

@dp.message(F.text == "💰 Пополнение")
async def dep(message: Message):
    await message.answer("💳 Для пополнения напишите @admin_support (Симуляция)")

@dp.message(F.text == "📋 Инфо")
async def info(message: Message):
    await message.answer("ℹ️ Shadow Store v1.0\nВсе права защищены.")

# --- ADMIN HANDLERS ---
@dp.message(F.text == "➕ Категория", F.from_user.id == ADMIN_ID)
async def adm_cat(message: Message, state: FSMContext):
    await message.answer("Введите имя категории:")
    await state.set_state(AdminStates.add_cat_name)

@dp.message(AdminStates.add_cat_name)
async def adm_cat_save(message: Message, state: FSMContext, session: AsyncSession):
    session.add(Category(name=message.text))
    await session.commit()
    await message.answer("✅ Категория создана!")
    await state.clear()

@dp.message(F.text == "➕ Товар", F.from_user.id == ADMIN_ID)
async def adm_prod(message: Message, state: FSMContext):
    await message.answer("Введите название товара:")
    await state.set_state(AdminStates.add_prod_name)

@dp.message(AdminStates.add_prod_name)
async def adm_p_name(message: Message, state: FSMContext):
    await state.update_data(n=message.text)
    await message.answer("Введите описание:")
    await state.set_state(AdminStates.add_prod_desc)

@dp.message(AdminStates.add_prod_desc)
async def adm_p_desc(message: Message, state: FSMContext):
    await state.update_data(d=message.text)
    await message.answer("Введите цену (число):")
    await state.set_state(AdminStates.add_prod_price)

@dp.message(AdminStates.add_prod_price)
async def adm_p_price(message: Message, state: FSMContext):
    try:
        await state.update_data(p=float(message.text))
        await message.answer("Введите контент (ссылка/текст):")
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
    await message.answer(f"📈 Пользователей: {u_count.scalar()}")

# --- STARTUP ---
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        res = await session.execute(select(Category))
        if not res.scalars().first():
            c = Category(name="Общее")
            session.add(c)
            await session.commit()
            await session.execute(select(c)) # refresh
            session.add(Product(category_id=c.id, name="Тест", description="Тест", price=10.0, content="TEST_DATA"))
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
