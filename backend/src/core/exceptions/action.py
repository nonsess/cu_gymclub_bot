from .base import ValidationException, ConflictException

class SelfActionException(ValidationException):
    def __init__(self):
        super().__init__("Cannot perform action on yourself", "SELF_ACTION_NOT_ALLOWED")

class ActionAlreadyRespondedException(ConflictException):
    def __init__(self, message: str = "Action already responded"):
        super().__init__(message)
        self.message = message