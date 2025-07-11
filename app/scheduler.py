from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from app.database.models import Schedule
from app.database.session import async_session
from logger import log_function, logger  
import asyncio


class ScheduleManager:
    @log_function
    def __init__(self, bot):
        self.scheduler = None
        self.bot = bot
        self._eventloop = None

    @log_function
    async def start(self):
        loop = asyncio.get_running_loop()
        self.scheduler = AsyncIOScheduler(event_loop=loop)
        self._eventloop = loop
        self.scheduler.start()
        logger.info('Планировщик запущен.')
        await self.load_jobs_from_db()

    @log_function
    def job_id(self, task_id: int) -> str:
        return f'task_{task_id}'

    @log_function
    async def load_jobs_from_db(self):
        async with async_session() as session:
            result = await session.execute(
                select(Schedule).where(Schedule.active == True)
            )
            tasks = result.scalars().all()
            logger.info(f'Загружено задач из БД: {len(tasks)}')

            for task in tasks:
                await self.add_job(task.id, task.user_id, task.text, task.time)

    @log_function
    async def add_job(self, task_id: int, user_id: int, text: str, time_obj):
        job_id = self.job_id(task_id)

        async def send():
            try:
                await self.bot.send_message(chat_id=user_id, text=text)
                logger.info(f'Сообщение отправлено пользователю {user_id} (задача {task_id})')
            except Exception as e:
                logger.warning(f'Не удалось отправить сообщение пользователю {user_id}: {e}')

        self.scheduler.add_job(
            self._wrap_async(send),
            trigger='cron',
            hour=time_obj.hour,
            minute=time_obj.minute,
            id=job_id,
            replace_existing=True
        )
        logger.info(f'Добавлена задача {task_id} для пользователя {user_id} на {time_obj.strftime('%H:%M')}')

    @log_function
    async def remove_job(self, task_id: int):
        job_id = self.job_id(task_id)
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f'Удалена задача {task_id} (job_id={job_id})')
        except Exception as e:
            logger.warning(f'Не удалось удалить задачу {task_id}: {e}')

    @log_function
    def _wrap_async(self, async_func):
        def wrapper():
            asyncio.run_coroutine_threadsafe(async_func(), self._eventloop)
        return wrapper
