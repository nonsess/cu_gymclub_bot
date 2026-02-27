from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_experience = State()
    waiting_for_about = State()
    waiting_for_photo = State()
    
    editing_profile = State()
    waiting_for_new_name = State()
    waiting_for_new_gender = State()
    waiting_for_new_age = State()
    waiting_for_new_experience = State()
    waiting_for_new_about = State()
    waiting_for_new_photos = State()
    waiting_for_hide_confirm = State()
