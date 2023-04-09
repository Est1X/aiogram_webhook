import logging
import os
import json
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, types
import requests

flask_hook = 'flask webhook'
TOKEN = 'bot token'
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

HEROKU_APP_NAME = 'aio32-app'
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=8000)

async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher):
    await bot.delete_webhook()

class UserState(StatesGroup):
    login= State()
    password = State()
@dp.message_handler(commands='start')
async def redirect_flask(message: types.Message):
    reg_button = KeyboardButton('Регистрация')
    in_button = KeyboardButton('Вход')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(reg_button,in_button)
    await message.answer(text ="Пройдите регистрацию для авторизации на сайте", reply_markup=keyboard)


class UserState(StatesGroup):
    login= State()
    password = State()


@dp.message_handler(text='Регистрация')
async def user_register(message: types.Message):
    await message.answer("Введите свой логин, от 5 до 14 символов")
    await UserState.login.set()

@dp.message_handler(text='Вход')
async def user_register(message: types.Message):
    button = InlineKeyboardButton('Авторизоваться', url='https://test-aio-app.herokuapp.com/')
    keyboard = InlineKeyboardMarkup(row_width=2).add(button)
    await message.answer('Перейти на сайт для авторизации',reply_markup=keyboard)

@dp.message_handler(state=UserState.login)
async def get_username(message: types.Message, state: FSMContext):
    if len(message.text) > 4 and len(message.text) < 15:
        await state.update_data(login=message.text)
        await message.answer("Введите пароль")
        await UserState.next()
    else:
        await message.answer("Не правильный логин, введите логин от 5 до 14 символов")
        await UserState.login.set()


@dp.message_handler(state=UserState.password)
async def get_address(message: types.Message, state: FSMContext):
    if len(message.text) > 4 and len(message.text) < 15:
        await state.update_data(password=message.text)
        data = await state.get_data()
        user_id = message.from_user.id
        user_username = message.from_user.first_name + ' ' + message.from_user.last_name
        user_tg = message.from_user.username
        login = data['login']
        password = data['password']
        req_data ={"login": login,"password":password, "user_id":user_id,"username":user_username,"user_tg":user_tg}
        r = requests.post(flask_hook, data=json.dumps(req_data),
                          headers={'content-type': 'application/json'})
        r.status_code
        await message.answer(f"Ваш логин: {data['login']}\n"
                             f"Ваш пароль: {data['password']}")
        await state.finish()
    else:
        await message.answer("Не правильный пароль, введите пароль от 5 до 14 символов")
        await UserState.password.set()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )