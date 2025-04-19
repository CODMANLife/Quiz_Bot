from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=option  # Здесь передаем сам текст ответа как callback_data
        ))

    builder.adjust(1)
    return builder.as_markup()