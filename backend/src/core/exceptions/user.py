from .base import ForbiddenException, UnauthorizedException, NotFoundException

class UserIsBanned(ForbiddenException):
    def __init__(self):
        super().__init__("User is banned")

class UserIsUnauthorized(UnauthorizedException):
    def __init__(self):
        super().__init__("User is unauthorized")

class UserNotFound(NotFoundException):
    def __init__(self):
        super().__init__("User not found")