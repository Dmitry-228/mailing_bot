from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import time

from app.states import CreateSchedule
from app.config import ADMINS
from app.database.session import SessionLocal
from app.database.models import Schedule

router = Router()
schedule_manager = None  # ← мы передадим его из app.py


def is_admin(message: Message) -> bool:
    return message.from_user.id in ADMINS


@router.message(Command('start'))
async def cmd_start(message: Message):
    if not is_admin(message):
        return
    await message.answer('Привет! Я бот для рассылок.\nНапиши /create чтобы создать новую. /jobs для просмотра запланированных задач.')


@router.message(Command('id'))
async def cmd_id(message: Message):
    await message.answer(f'Ваш Telegram ID: {message.from_user.id}')


@router.message(Command('create'))
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

        # Сохраняем в БД
        session = SessionLocal()
        task = Schedule(user_id=user_id, text=text, time=t, active=True)
        session.add(task)
        session.commit()

        # Добавляем в планировщик
        schedule_manager.add_job(task.id, user_id, text, t)

        await message.answer(f'Рассылка создана и запланирована на {t.strftime('%H:%M')}')
        await state.clear()
    except Exception:
        await message.answer('Неверный формат времени. Попробуйте снова: ЧЧ:ММ')


@router.message(Command('jobs'))
async def cmd_jobs(message: Message):
    if not is_admin(message):
        return

    from app.database.session import SessionLocal
    from app.database.models import Schedule

    session = SessionLocal()
    tasks = session.query(Schedule).all()
    session.close()

    if not tasks:
        await message.answer('📭 Нет задач в базе.')
        return

    text = 'Задачи в БД:\n'
    for task in tasks:
        status = 'Активна' if task.active else 'Отключена'
        text += f'\nID {task.id} | TIME {task.time.strftime('%H:%M')} | {status}\nTEXT: {task.text[:30]}...\n'

    # список запланированных задач
    text += '\n🕒 Запланированные задачи:\n'
    jobs = schedule_manager.scheduler.get_jobs()
    if not jobs:
        text += 'Нет активных задач.\n'
    else:
        for job in jobs:
            next_run = job.next_run_time.strftime('%H:%M') if job.next_run_time else '—'
            text += f'• {job.id} → ⏱ {next_run}\n'

    await message.answer(text)
