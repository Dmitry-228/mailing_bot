import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import BOT_TOKEN
from app.scheduler import ScheduleManager
from app import handlers
from app.database.models import Base
from app.database.session import engine

async def main():
    # Создаём бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Инициализируем таблицы (один раз)
    Base.metadata.create_all(bind=engine)

    # Планировщик рассылок
    schedule_manager = ScheduleManager(bot)
    schedule_manager.start()

    # Передаём планировщик в хендлер
    handlers.schedule_manager = schedule_manager
    dp.include_router(handlers.router)

    print('Бот запущен')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
