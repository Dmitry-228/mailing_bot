from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_button = KeyboardButton(text="СТАРТ")

admin_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="СОЗДАТЬ"),
            KeyboardButton(text="СПИСОК РАССЫЛОК"),
        ],
        [
            KeyboardButton(text="УДАЛИТЬ РАССЫЛКУ"),
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)
