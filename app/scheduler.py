from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from app.database.models import Schedule
from app.database.session import SessionLocal
import asyncio


class ScheduleManager:
    def __init__(self, bot):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot
        self.loop = asyncio.get_event_loop()

    def start(self):
        self.scheduler.start()
        self.load_jobs_from_db()

    def load_jobs_from_db(self):
        session: Session = SessionLocal()
        tasks = session.query(Schedule).filter_by(active=True).all()

        for task in tasks:
            self.add_job(task.id, task.user_id, task.text, task.time)

        session.close()

    def add_job(self, task_id: int, user_id: int, text: str, time_obj):
        job_id = f'task_{task_id}'

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
            id=job_id
        )

    def _wrap_async(self, async_func):
        def wrapper():
            print(f'[🌀] Вызван wrapper() для async-задачи')
            try:
                self.loop.create_task(async_func())
                print('[✅] Задача успешно запущена через create_task()')
            except Exception as e:
                print(f'[❌] Ошибка при запуске задачи: {e}')

        return wrapper
