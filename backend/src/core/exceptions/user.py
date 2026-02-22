from .base import ConflictException, NotFoundException

class UserNotFoundException(NotFoundException):
    def __init__(self, user_id: int = None, telegram_id: str = None):
        if user_id:
            message = f"User with id {user_id} not found"
        elif telegram_id:
            message = f"User with telegram_id {telegram_id} not found"
        else:
            message = "User not found"
        super().__init__(message, "USER_NOT_FOUND")

class UserAlreadyExistsException(ConflictException):
    def __init__(self, telegram_id: str):
        super().__init__(f"User with telegram_id {telegram_id} already exists", "USER_ALREADY_EXISTS")
