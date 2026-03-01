from src.core.exceptions.base import ForbiddenException

class InvalidPermissions(ForbiddenException):
    def __init__(self):
        super().__init__("Not enought rights")
