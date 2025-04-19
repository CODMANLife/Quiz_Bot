#@title Полный код бота для самоконтроля
import asyncio
import aiosqlite
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters import Command
from config import API_TOKEN, DB_NAME
from database import create_table, get_quiz_index, update_quiz_index, save_user_score, get_stats
from quiz_data import quiz_data
from keyboards import generate_options_keyboard

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

user_scores = {}

@dp.callback_query(F.data)
async def answer(callback: types.CallbackQuery):
    selected_answer = callback.data
    
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']
    correct_answer = quiz_data[current_question_index]['options'][correct_option]

    await callback.message.answer(f"Ваш ответ: {selected_answer}")

    if selected_answer == correct_answer:
        await callback.message.answer("Верно!")
        user_scores[callback.from_user.id] = user_scores.get(callback.from_user.id, 0) + 1
    else:
        await callback.message.answer(f"Неправильно. Правильный ответ: {correct_answer}")

    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        score = user_scores.get(callback.from_user.id, 0)
        await save_user_score(callback.from_user.id, score)
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен!\nВаш результат: {score}/{len(quiz_data)}")
        user_scores[callback.from_user.id] = 0

# Хендлер для статистики
@dp.message(Command("stats"))
async def stats(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT score FROM quiz_results WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                await message.answer(f"Ваш последний результат: {row[0]}/{len(quiz_data)}")
            else:
                await message.answer("У вас пока нет сохранённых результатов.")


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))


async def get_question(message, user_id):

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)
    await get_question(message, user_id)


# Хэндлер на команду /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):

    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)

# Запуск процесса поллинга новых апдейтов
async def main():

    # Запускаем создание таблицы базы данных
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())