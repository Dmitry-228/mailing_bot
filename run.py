import asyncio 
from aiogram import Bot, Dispatcher 
from aiogram.fsm.storage.memory import MemoryStorage 
 
from app.config import BOT_TOKEN 
from app.scheduler import ScheduleManager 
from app import handlers 
from app.database.models import Base 
from app.database.session import engine 
 
import logging 
 
logging.basicConfig(level=logging.INFO) 
 
async def main(): 
    # Создаём бота и диспетчер 
    bot = Bot(token=BOT_TOKEN) 
    dp = Dispatcher(storage=MemoryStorage()) 

    # Инициализируем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Планировщик рассылок 
    schedule_manager = ScheduleManager(bot) 
    await schedule_manager.start() 

    # Передаём планировщик в хендлер через функцию
    handlers.set_schedule_manager(schedule_manager)
    dp.include_router(handlers.router) 
 
    print('Бот запущен') 
    await dp.start_polling(bot) 
 
if __name__ == '__main__': 
    asyncio.run(main())
