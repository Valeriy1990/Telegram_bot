import aiosqlite

async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Выполняем SQL-запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER)''')
        # Сохраняем изменения
        await db.commit()

    async with aiosqlite.connect('stats.db') as db:
        # Создаём таблицу результатов
        await db.execute('''CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, user_id INTEGER, wrong_count INTEGER, right_count INTEGER)''')
        # Сохраняем изменения
        await db.commit()


async def update_quiz_index(user_id, index):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index) VALUES (?, ?)', (user_id, index))
        # Сохраняем изменения
        await db.commit()
        
async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect('quiz_bot.db') as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0
            
async def start_stats(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect('stats.db') as db:
        # Вставляем новую запись
        await db.execute('INSERT INTO stats (user_id, wrong_count, right_count) VALUES (?, ?, ?)', (user_id, 0, 0))
        # Сохраняем изменения
        await db.commit()


async def get_stats_index():
     # Подключаемся к базе данных
     async with aiosqlite.connect('stats.db') as db:
        # Возвращаем индекс последней записи в таблице результатов
        async with db.execute('''SELECT id FROM stats ORDER BY id DESC LIMIT 1''') as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

async def set_stats(id_quiz, res: bool):
     # Подключаемся к базе данных
     async with aiosqlite.connect('stats.db') as db:
        # Вставляем новую запись
        if res:
            await db.execute('''UPDATE stats
                             SET right_count = right_count + 1
                             WHERE id = (?) ''', (id_quiz,))
        else:
            await db.execute('''UPDATE stats
                             SET wrong_count = wrong_count + 1
                             WHERE id = (?) ''', (id_quiz,))
        # Сохраняем изменения
        await db.commit()

async def get_stats(id_quiz):
     # Подключаемся к базе данных
     async with aiosqlite.connect('stats.db') as db:
        # Получаем запись для заданного квиза
        async with db.execute('''SELECT id FROM stats WHERE id = (?)''', (id_quiz)) as cursor:
        # Возвращаем результат квиза
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
