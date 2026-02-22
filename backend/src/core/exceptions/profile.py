from .base import ConflictException, NotFoundException

class ProfileNotFoundException(NotFoundException):
    def __init__(self, profile_id: int = None, user_id: int = None):
        if profile_id:
            message = f"Profile with id {profile_id} not found"
        elif user_id:
            message = f"Profile for user {user_id} not found"
        else:
            message = "Profile not found"
        super().__init__(message, "PROFILE_NOT_FOUND")

class ProfileAlreadyExistsException(ConflictException):
    def __init__(self, user_id: int):
        super().__init__(f"Profile already exists for user {user_id}", "PROFILE_ALREADY_EXISTS")

class NoMoreProfilesException(NotFoundException):
    def __init__(self):
        super().__init__("No more profiles available", "NO_MORE_PROFILES")
