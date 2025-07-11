import asyncio
from logger import logger

from app.database.models import Base
from app.database.session import engine
from bot import bot, dp, schedule_manager

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await schedule_manager.start()

    logger.info('Бот запущен')

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info('Бот остановлен через терминал')
    finally:
        logger.info('Завершаем работу')
        try:
            scheduler = schedule_manager.scheduler
            if scheduler is not None:
                await scheduler.shutdown()
                logger.info('Планировщик остановлен')
            else:
                logger.info('Планировщик не был инициализирован')
        except Exception as e:
            logger.error(f'Ошибка при завершении планировщика: {e}')
        try:
            await bot.session.close()
            logger.info('Сессия бота закрыта')
        except Exception as e:
            logger.error(f'Ошибка при закрытии сессии бота: {e}')
        try:
            await engine.dispose()
            logger.info('Соединение с БД закрыто')
        except Exception as e:
            logger.error(f'Ошибка при закрытии соединения с БД: {e}')
        logger.info('Бот, планировщик и соединение с БД завершены корректно')

if __name__ == '__main__':
    asyncio.run(main())
