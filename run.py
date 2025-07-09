import asyncio 
from aiogram import Bot, Dispatcher 
from aiogram.fsm.storage.memory import MemoryStorage 
 
from app.config import BOT_TOKEN 
from app.scheduler import ScheduleManager 
from app import handlers 
from app.database.models import Base 
from app.database.session import engine 
 
import logging 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

async def main(): 
    bot = Bot(token=BOT_TOKEN) 
    dp = Dispatcher(storage=MemoryStorage()) 
    async with engine.begin() as conn:       # Инициализируем таблицы
        await conn.run_sync(Base.metadata.create_all)

    schedule_manager = ScheduleManager(bot) 
    await schedule_manager.start() 

    handlers.set_schedule_manager(schedule_manager)
    dp.include_router(handlers.router) 
 
    print('Бот запущен') 
    await dp.start_polling(bot) 
 
if __name__ == '__main__': 
    asyncio.run(main())
