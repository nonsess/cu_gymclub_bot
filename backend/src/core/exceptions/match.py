from .base import NotFoundException, ConflictException

class MatchNotFoundException(NotFoundException):
    def __init__(self, match_id: int):
        super().__init__(f"Match with id {match_id} not found", "MATCH_NOT_FOUND")

class MatchAlreadyExistsException(ConflictException):
    def __init__(self, user1_id: int, user2_id: int):
        super().__init__(f"Match already exists between users {user1_id} and {user2_id}", "MATCH_ALREADY_EXISTS")
