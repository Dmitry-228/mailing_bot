from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import time
from sqlalchemy import select
import logging

from app.states import CreateSchedule, DeleteSchedule
from config import ADMINS
from app.database.session import async_session
from app.database.models import Schedule
from app.scheduler import ScheduleManager
from app.keyboards import admin_main_menu


router = Router()
schedule_manager: ScheduleManager = None
logger = logging.getLogger(__name__)


def set_schedule_manager(manager: ScheduleManager):
    global schedule_manager
    schedule_manager = manager


def is_admin(message: Message) -> bool:
    return message.from_user.id in ADMINS


@router.message(F.text == 'СТАРТ')
async def handle_start_button(message: Message):
    await message.answer(
        'Добро пожаловать!',
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command('start'))
async def cmd_start(message: Message):
    if not is_admin(message):
        return
    await message.answer('Привет! Я бот для рассылок. Выберите действие:', reply_markup=admin_main_menu)


@router.message(Command('id'))
async def cmd_id(message: Message):
    await message.answer(f'Ваш Telegram ID: {message.from_user.id}')


@router.message(Command('create'))
@router.message(F.text == 'СОЗДАТЬ')
async def cmd_create(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await message.answer('Введите текст сообщения для рассылки:')
    await state.set_state(CreateSchedule.waiting_for_text)


@router.message(CreateSchedule.waiting_for_text)
async def fsm_get_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer('Введите время в формате ЧЧ:ММ (24ч):')
    await state.set_state(CreateSchedule.waiting_for_time)


@router.message(CreateSchedule.waiting_for_time)
async def fsm_get_time(message: Message, state: FSMContext):
    try:
        parts = message.text.split(':')
        hour = int(parts[0])
        minute = int(parts[1])

        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError('Некорректное время')
    
        t = time(hour=hour, minute=minute)

        data = await state.get_data()
        text = data['text']
        user_id = message.from_user.id

        # Сохраняем в БД (асинхронно)
        async with async_session() as session:
            task = Schedule(user_id=user_id, text=text, time=t, active=True)
            session.add(task)
            await session.commit()
            await session.refresh(task)
        logger.info(f'Создана рассылка: user_id={user_id}, task_id={task.id}, time={t}')
        # Добавляем в планировщик
        await schedule_manager.add_job(task.id, user_id, text, t)
        logger.info(f'Задача добавлена в планировщик: task_id={task.id}')

        await message.answer(f'Рассылка создана и запланирована на {t.strftime('%H:%M')}')
        await state.clear()
    except Exception as e:
        logger.exception(f'Ошибка при создании рассылки: {e}')
        await message.answer('Неверный формат времени. Попробуйте снова: ЧЧ:ММ')


@router.message(Command('jobs'))
@router.message(F.text == 'СПИСОК РАССЫЛОК')
async def cmd_jobs(message: Message):
    if not is_admin(message):
        return

    async with async_session() as session:
        result = await session.execute(select(Schedule))
        tasks = result.scalars().all()

    if not tasks:
        await message.answer('Нет задач в базе.')
        return

    text = 'Задачи в БД:\n'
    for task in tasks:
        status = 'Активна' if task.active else 'Отключена'
        text += f'\nID {task.id} | TIME {task.time.strftime('%H:%M')} | {status}\nTEXT: {task.text[:30]}...\n'

    text += '\nЗапланированные задачи:\n'
    jobs = schedule_manager.scheduler.get_jobs()
    if not jobs:
        text += 'Нет активных задач.\n'
    else:
        for job in jobs:
            next_run = job.next_run_time.strftime('%H:%M') if job.next_run_time else '—'
            text += f'• {job.id} → {next_run}\n'

    logger.info(f'Пользователь {message.from_user.id} запросил список задач')
    await message.answer(text)


@router.message(Command('delete'))
@router.message(F.text == 'УДАЛИТЬ РАССЫЛКУ')
async def delete_command(message: Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(select(Schedule).where(Schedule.user_id == message.from_user.id))
        tasks = result.scalars().all()

    if not tasks:
        await message.answer('У вас нет активных рассылок.')
        return

    text = 'Введите ID рассылки, которую хотите удалить:\n\n'
    for task in tasks:
        text += f"\nID {task.id} | TIME {task.time.strftime('%H:%M')} | TEXT: {task.text[:30]}...\n"

    await message.answer(text)
    await state.set_state(DeleteSchedule.waiting_for_task_id)
    logger.info(f'Пользователь {message.from_user.id} запросил удаление рассылки')


@router.message(DeleteSchedule.waiting_for_task_id)
async def process_delete(message: Message, state: FSMContext):
    try:
        task_id = int(message.text.strip())
    except ValueError:
        logger.warning(f'Пользователь {message.from_user.id} ввёл неверный ID для удаления')
        await message.answer('Неверный ID. Введите число.')
        return
    async with async_session() as session:
        result = await session.execute(
            select(Schedule).where(Schedule.id == task_id, Schedule.user_id == message.from_user.id)
        )
        task = result.scalars().first()
        if not task:
            logger.warning(f'Пользователь {message.from_user.id} попытался удалить несуществующую рассылку ID {task_id}')
            await message.answer('Рассылка не найдена')
            await state.clear()
            return
        await session.delete(task)
        await session.commit()
    logger.info(f'Пользователь {message.from_user.id} удалил рассылку ID {task_id}')
    await schedule_manager.remove_job(task_id)
    await message.answer(f'Рассылка с ID {task_id} удалена.')
    await state.clear()
