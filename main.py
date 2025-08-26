import asyncio
import logging
from aiogram import F
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from environs import Env

from for_SQL import create_table, update_quiz_index, get_quiz_index, start_stats, set_stats, get_stats_index, get_stats
from for_keyboard import generate_options_keyboard
from for_quiz import *
from for_queue import *
                         
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

 # Создаем экземпляр класса Env
env: Env = Env()
# Добавляем в переменные окружения данные, прочитанные из файла .env 
env.read_env(r'C:\Users\vbekr\Desktop\Python\Telegram_bot\my_env.env')

API_TOKEN = env('API_TOKEN')

# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать игру"))
    # Прикрепляем кнопки к сообщению
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))
    
# Хэндлер на команду /last_stats
@dp.message(Command("last_stats"))
async def get_last_stats(message: types.Message):
    # Получаем id последнего значения таблицы результатов
    id_quiz = await get_stats_index()
    # Получаем результат из таблицы результатов
    stat = await get_stats(id_quiz)
    for quiz in stat:
        await message.answer(f"Игроком под номером {quiz[1]} всего сыграно {quiz[0]} игр\n Сумма неверных ответов: {quiz[2]}\n Сумма верных ответов: {quiz[3]}")

# Хэндлер на команды /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    # Отправляем новое сообщение без кнопок
    await message.answer(f"Давайте начнем квиз!")

    # Запускаем новый квиз
    await new_quiz(message)
    
async def new_quiz(message):
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id

    # Создаём новую запись в таблице результатов
    await start_stats(user_id)
    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)

    # запрашиваем новый вопрос для квиза
    await get_question(message, user_id)

async def get_question(message, user_id):

    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = quiz_data[current_question_index]['correct_option']
    # Получаем список вариантов ответа для текущего вопроса
    opts = quiz_data[current_question_index]['options']

    # Функция генерации кнопок для текущего вопроса квиза
    # В качестве аргументов передаем варианты ответов и значение правильного ответа (не индекс!)
    kb = generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)   

@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    item = callback.from_user.id, callback.message.text, callback.message.reply_markup.inline_keyboard[0][0].text

    await add_item(item)

    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    # Получаем id последнего значения таблицы результатов
    id_quiz = await get_stats_index()

    # Отправляем в чат сообщение, что ответ верный
    await callback.message.answer("Верно!")

    # Записываем положительный результат в таблицу результатов
    await set_stats(id_quiz, res = True)

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        stat = await get_stats(id_quiz)
        # Уведомление об окончании квиза
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен!\nНеверных ответов: {stat[-1][2]}\nВерных ответов: {stat[-1][3]}")
        # res_answere = flush_buffer(callback.message)
        # await callback.message.answer(f"Вопрос: {res_answere[1]}\nВаш ответ: {res_answere[2]}")

        await flush_buffer(callback.message)

@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    item = callback.from_user.id, callback.message.text, callback.message.reply_markup.inline_keyboard[0][0].text

    await add_item(item)
    
    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    correct_option = quiz_data[current_question_index]['correct_option']

    # Отправляем в чат сообщение об ошибке с указанием верного ответа
    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    # Получаем id последнего значения таблицы результатов
    id_quiz = await get_stats_index()

    # Записываем отрицательный результат в таблицу результатов
    await set_stats(id_quiz, res = False)

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        stat = await get_stats(id_quiz)

        # Уведомление об окончании квиза
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен!\nНеверных ответов: {stat[-1][2]}\nВерных ответов: {stat[-1][3]}")
        # res_answere = await consumer(answers)
        # # await callback.message.answer(f"Вопрос: {res_answere[1]}\nВаш ответ: {res_answere[2]}")
        # await callback.message.answer(f"{type(res_answere)}")    

        await flush_buffer(callback.message)

# Запуск процесса поллинга новых апдейтов
async def main():

    # Запускаем создание таблицы базы данных
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())