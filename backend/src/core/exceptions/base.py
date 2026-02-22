class DomainException(Exception):
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)

class NotFoundException(DomainException):
    def __init__(self, message: str, code: str = None):
        super().__init__(message, code or "NOT_FOUND")

class ConflictException(DomainException):
    def __init__(self, message: str, code: str = None):
        super().__init__(message, code or "CONFLICT")

class ValidationException(DomainException):
    def __init__(self, message: str, code: str = None):
        super().__init__(message, code or "VALIDATION_ERROR")
