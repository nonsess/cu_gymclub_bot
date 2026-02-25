from .base import ValidationException

class SelfActionException(ValidationException):
    def __init__(self):
        super().__init__("Cannot perform action on yourself", "SELF_ACTION_NOT_ALLOWED")
