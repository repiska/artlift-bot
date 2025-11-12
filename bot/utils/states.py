"""Состояния FSM для диалогов"""
from aiogram.fsm.state import State, StatesGroup


class ApplicationStates(StatesGroup):
    """Состояния процесса подачи заявки"""
    waiting_for_confirmation = State()
    user_question = State()


class MessageEditStates(StatesGroup):
    """Состояния для редактирования сообщений"""
    waiting_for_new_content = State()


class QuestionStates(StatesGroup):
    """Состояния для вопросов пользователей"""
    waiting_for_question = State()
    waiting_for_answer = State()

