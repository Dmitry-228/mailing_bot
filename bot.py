from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from app.scheduler import ScheduleManager
from app import handlers

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

schedule_manager = ScheduleManager(bot)
handlers.set_schedule_manager(schedule_manager)

dp.include_router(handlers.router)
