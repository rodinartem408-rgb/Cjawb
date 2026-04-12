import asyncio
import logging
import os
from datetime import datetime
from typing import Union, List, Optional

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    CallbackQuery,
    Message
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy import BigInteger, String, Float, ForeignKey, Text, DateTime, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from redis.asyncio import Redis

# --- CONFIGURATION ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///db.sqlite3")

# --- DATABASE MODELS ---
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    referrer_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    orders: Mapped[list['Order']] = relationship(back_populates='user')
    transactions: Mapped[list['Transaction']] = relationship(back_populates='user')

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
    content: Mapped[str] = mapped_column(Text)  # Link to file or text content
    image_id: Mapped[str] = mapped_column(String, nullable=True) # Telegram file_id
    
    category: Mapped['Category'] = relationship(back_populates='products')

class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped['User'] = relationship(back_populates='orders')

class Transaction(Base):
    __tablename__ = 'transactions'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    amount: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String)  # 'deposit', 'withdraw', 'purchase'
    status: Mapped[str] = mapped_column(String) # 'completed', 'pending'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped['User'] = relationship(back_populates='transactions')

# --- DATABASE ENGINE ---
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# --- FSM STATES ---
class ShopStates(StatesGroup):
    buying_product = State()
    searching_category = State()

class AdminStates(StatesGroup):
    adding_category_name = State()
    adding_product_name = State()
    adding_product_desc = State()
    adding_product_price = State()
    adding_product_content = State()
    adding_product_image = State()
    broadcasting = State()

class DepositStates(StatesGroup):
    waiting_for_amount = State()

# --- KEYBOARDS ---
def main_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🛒 Магазин")],
        [KeyboardButton(text="💰 Пополнение"), KeyboardButton(text="💸 Вывод")],
        [KeyboardButton(text="👤 Личный кабинет"), KeyboardButton(text="📋 Информация")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def admin_menu_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="➕ Добавить категорию"), KeyboardButton(text="➕ Добавить товар")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📢 Рассылка")],
        [KeyboardButton(text="👥 Пользователи")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def back_button(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=prefix))
    return builder.as_markup()

# --- DATABASE UTILS ---
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        # Seed Check
        res = await session.execute(select(Category))
        if not res.scalars().first():
            # Initial Seed Data
            cat1 = Category(name="Базы чатов")
            cat2 = Category(name="Софт")
            cat3 = Category(name="Мануалы")
            cat4 = Category(name="Услуги")
            session.add_all([cat1, cat2, cat3, cat4])
            await session.flush()
            
            p1 = Product(category_id=cat1.id, name="TG VIP Base", description="10k channels", price=50.0, content="https://t.me/example_link")
            p2 = Product(category_id=cat2.id, name="Parser Pro", description="Best parser", price=120.0, content="https://t.me/file_link")
            p3 = Product(category_id=cat3.id, name="Carding Guide", description="Step by step", price=30.0, content="https://t.me/manual_link")
            session.add_all([p1, p2, p3])
            await session.commit()
