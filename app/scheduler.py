from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from app.database.models import Schedule
from app.database.session import async_session
import asyncio


class ScheduleManager:
    def __init__(self, bot):
        self.scheduler = None
        self.bot = bot
        self._eventloop = None

    async def start(self):
        loop = asyncio.get_running_loop()
        self.scheduler = AsyncIOScheduler(event_loop=loop)
        self._eventloop = loop
        self.scheduler.start()
        await self.load_jobs_from_db()

    def job_id(self, task_id: int) -> str:
        return f"task_{task_id}"

    async def load_jobs_from_db(self):
        async with async_session() as session:
            result = await session.execute(
                select(Schedule).where(Schedule.active == True)
            )
            tasks = result.scalars().all()
            for task in tasks:
                await self.add_job(task.id, task.user_id, task.text, task.time)

    async def add_job(self, task_id: int, user_id: int, text: str, time_obj):
        job_id = self.job_id(task_id)

        async def send():
            try:
                await self.bot.send_message(chat_id=user_id, text=text)
                print(f'Рассылка для пользователя {user_id} отправлена')
            except Exception as e:
                print(f'Ошибка отправки сообщения {user_id}: {e}')

        self.scheduler.add_job(
            self._wrap_async(send),
            trigger='cron',
            hour=time_obj.hour,
            minute=time_obj.minute,
            id=job_id,
            replace_existing=True
        )
        print(f"Задача {job_id} добавлена на {time_obj.strftime('%H:%M')}")

    async def remove_job(self, task_id: int):
        job_id = self.job_id(task_id)
        try:
            self.scheduler.remove_job(job_id)
            print(f"Задача {job_id} удалена из планировщика")
        except Exception as e:
            print(f"Ошибка при удалении задачи {job_id}: {e}")

    def _wrap_async(self, async_func):
        def wrapper():
            print(f'Вызван wrapper() для async-задачи')
            try:
                asyncio.run_coroutine_threadsafe(async_func(), self._eventloop)
            except Exception as e:
                print(f'Ошибка при запуске задачи: {e}')
        return wrapper
