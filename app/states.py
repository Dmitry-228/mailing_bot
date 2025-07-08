from aiogram.fsm.state import StatesGroup, State

class CreateSchedule(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()

class DeleteSchedule(StatesGroup):
    waiting_for_task_id = State()