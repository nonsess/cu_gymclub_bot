from .base import ConflictException, ValidationException

class ActionAlreadyExistsException(ConflictException):
    def __init__(self, from_user_id: int, to_user_id: int):
        super().__init__(
            f"Action from user {from_user_id} to user {to_user_id} already exists",
            "ACTION_ALREADY_EXISTS"
        )

class SelfActionException(ValidationException):
    def __init__(self):
        super().__init__("Cannot perform action on yourself", "SELF_ACTION_NOT_ALLOWED")
