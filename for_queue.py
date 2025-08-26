import asyncio

buffer = []
buffer_lock = asyncio.Lock()

async def add_item(item):
    async with buffer_lock:
        buffer.append(item)

async def flush_buffer(message):
    # сначала забираем данные под замком, затем отправляем вне замка
    async with buffer_lock:
        if not buffer:
            return
        for item in buffer:
            text = f'На вопрос: {item[1]}\nВы ответили: {item[2]}'
            await message.answer(text)
        buffer.clear()