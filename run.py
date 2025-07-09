import asyncio 
from aiogram import Bot, Dispatcher 
from aiogram.fsm.storage.memory import MemoryStorage 
 
from config import BOT_TOKEN 
from app.scheduler import ScheduleManager 
from app import handlers 
from app.database.models import Base 
from app.database.session import engine 
 
import logging 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
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
    try:
        await dp.start_polling(bot)
    finally:
        logging.info('Завершаем работу...')
        try:
            await schedule_manager.scheduler.shutdown()
        except Exception as e:
            logging.error(f'Ошибка при завершении планировщика: {e}')
        try:
            await bot.session.close()
        except Exception as e:
            logging.error(f'Ошибка при закрытии сессии бота: {e}')
        try:
            await engine.dispose()
        except Exception as e:
            logging.error(f'Ошибка при закрытии соединения с БД: {e}')
        logging.info('Бот, планировщик и соединение с БД корректно завершены.')

if __name__ == '__main__':
    asyncio.run(main())
