from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.command import Command
import asyncio
import json
import os

API_TOKEN = "7971162900:AAH4vsTQOr4fYrhLSbWNjXr9tiLwj1pO82k"
ADMIN_ID = 6631055683

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot)

ref = 0
CHANNELS = ["@stargift_channel"]

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

referrals = load_json("referrals.json")
ballances = load_json("ballances.json")
user_gift_selection = load_json("gifts.json")
users = load_json("users.json")  # Новый файл

async def check_subscriptions(user_id):
    for channel in CHANNELS:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        if member.status in ("left", "kicked"):
            return False
    return True

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username

    if not await check_subscriptions(user_id):
        buttons = [
            [InlineKeyboardButton(text="Подписаться на канал", url="https://t.me/stargift_channel")],
            [InlineKeyboardButton(text="Я подписался", callback_data="check_subs")]
        ]
        await message.answer(
            "Чтобы пользоваться ботом, подпишись на наш канал:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        return

    first_time_user = str(user_id) not in users
    if first_time_user:
        users[str(user_id)] = True
        save_json("users.json", users)

        if str(user_id) not in ballances:
            ballances[str(user_id)] = 0
            save_json("ballances.json", ballances)

        parts = message.text.strip().split()
        if len(parts) > 1:
            inviter_id = parts[1]

            if inviter_id.isdigit():
                inviter_id_int = int(inviter_id)

                if inviter_id_int != user_id:
                    if inviter_id not in referrals:
                        referrals[inviter_id] = []

                    if str(user_id) not in referrals[inviter_id]:
                        referrals[inviter_id].append(str(user_id))
                        save_json("referrals.json", referrals)

                        global ref
                        ref += 1

                        if str(inviter_id_int) not in ballances:
                            ballances[str(inviter_id_int)] = 0
                        ballances[str(inviter_id_int)] += 15
                        save_json("ballances.json", ballances)

                        try:
                            await bot.send_message(
                                chat_id=inviter_id_int,
                                text=f"Пользователь @{username} зашёл в бота по твоей ссылке! +15⭐️"
                            )
                        except Exception as e:
                            print(f"Не удалось отправить сообщение пригласившему: {e}")

    kb = [
        [types.KeyboardButton(text="Профиль")],
        [types.KeyboardButton(text="Магазин")],
        [types.KeyboardButton(text="Рефка")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Привет!", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "check_subs")
async def check_again(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    kb = [
        [types.KeyboardButton(text="Профиль")],
        [types.KeyboardButton(text="Магазин")],
        [types.KeyboardButton(text="Рефка")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    if await check_subscriptions(user_id):
        await callback_query.message.answer("Спасибо за подписку!", reply_markup=keyboard)
        await send_welcome(callback_query.message)
    else:
        await callback_query.message.answer("Ты подписан не на все каналы!")
    await callback_query.answer()

@dp.message(F.text == "Рефка")
async def send_ref(message: types.Message):
    await message.answer(f"Держи реферальную ссылку!\nhttps://t.me/kiberly74_bot?start={message.from_user.id}")

@dp.message(F.text == "Профиль")
async def send_portfolio(message: types.Message):
    user_id = str(message.from_user.id)
    bal = ballances.get(user_id, 0)
    invited = sum([1 for users in referrals.values() if user_id in users])
    await message.answer(f"Ты уже пригласил человек: {invited}\nУ тебя на балике - {bal}⭐️")

@dp.message(F.text == "Магазин")
async def send_shop(message: types.Message):
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💝 Сердечко, 15⭐️", callback_data="сердце")],
        [InlineKeyboardButton(text="🧸 Мишка, 15⭐️", callback_data="мишка")]
    ])
    await message.answer("Сейчас в магазине:", reply_markup=inline_kb)

@dp.callback_query(lambda c: c.data in ["мишка", "сердце"])
async def gift_callback(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    gift = callback_query.data

    if ballances.get(user_id, 0) < 15:
        await callback_query.message.answer("Недостаточно звёзд для покупки!")
        await callback_query.answer()
        return

    ballances[user_id] -= 15
    save_json("ballances.json", ballances)

    user_gift_selection[user_id] = gift
    save_json("gifts.json", user_gift_selection)

    await callback_query.message.answer("Введите юзернейм получателя:\n\nВАЖНО: если имя пользователя будет введено неверно, заявка будет отклонена!")
    await callback_query.answer()

@dp.message(F.text)
async def handle_username(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in user_gift_selection:
        gift = user_gift_selection.pop(user_id)
        save_json("gifts.json", user_gift_selection)

        inline_kb_admin = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Принять", callback_data=f"accept:{user_id}")],
            [InlineKeyboardButton(text="Отклонить", callback_data=f"reject:{user_id}")]
        ])
        await message.answer("Твоя заявка отправлена!")
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"Заявка от @{message.from_user.username} на подарок '{gift}'",
                reply_markup=inline_kb_admin
            )
        except Exception as e:
            print(f"Ошибка при отправке админу: {e}")

@dp.callback_query(lambda c: c.data.startswith("reject:"))
async def reject_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(":")[1])
    try:
        await bot.send_message(user_id, "К сожалению, твоя заявка была отклонена :(")
    except Exception as e:
        print(f"Ошибка при уведомлении пользователя: {e}")
    await callback_query.answer("Отклонено.")

@dp.callback_query(lambda c: c.data.startswith("accept:"))
async def accept_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(":")[1])
    try:
        await bot.send_message(user_id, "Твоя заявка была принята! :)")
    except Exception as e:
        print(f"Ошибка при уведомлении пользователя: {e}")
    await callback_query.answer("Принято.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
