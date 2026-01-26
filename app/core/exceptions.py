from fastapi.exceptions import HTTPException


class AlreadyExistsError(HTTPException):
    def __init__(self, detail: str = "Already exists"):
        super().__init__(status_code=400, detail=detail)

class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Not found"):
        super().__init__(status_code=404, detail=detail)

class UserAlreadyExistsError(HTTPException):
    def __init__(self, detail: str = "User already exists"):
        super().__init__(status_code=400, detail=detail)


class UserNotFoundError(HTTPException):
    def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=404, detail=detail)


class InvalidCredentialsError(HTTPException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(status_code=401, detail=detail)

class EmailAlreadyExistsError(HTTPException):
    def __init__(self, detail: str = "Email already exists"):
        super().__init__(status_code=400, detail=detail)


class PhoneAlreadyExistsError(HTTPException):
    def __init__(self, detail: str = "Phone already exists"):
        super().__init__(status_code=400, detail=detail)


class UserNameAlreadyExistsError(HTTPException):
    def __init__(self, detail: str = "Username already exists"):
        super().__init__(status_code=400, detail=detail)

class InvalidEmailError(HTTPException):
    def __init__(self, detail: str = "Invalid email"):
        super().__init__(status_code=400, detail=detail)

class InvalidPhoneError(HTTPException):
    def __init__(self, detail: str = "Invalid phone"):
        super().__init__(status_code=400, detail=detail)

class InvalidUserNameError(HTTPException):
    def __init__(self, detail: str = "Invalid username"):
        super().__init__(status_code=400, detail=detail)

class InvalidPasswordError(HTTPException):
    def __init__(self, detail: str = "Invalid password"):
        super().__init__(status_code=400, detail=detail)


class ValidationError(HTTPException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=400, detail=detail)


class InvalidResetTokenError(HTTPException):
    def __init__(self, detail: str = "Invalid or expired reset token"):
        super().__init__(status_code=400, detail=detail)


class ResetTokenExpiredError(HTTPException):
    def __init__(self, detail: str = "Reset token has expired"):
        super().__init__(status_code=400, detail=detail)


class ResetTokenAlreadyUsedError(HTTPException):
    def __init__(self, detail: str = "Reset token has already been used"):
        super().__init__(status_code=400, detail=detail)


class PasswordMismatchError(HTTPException):
    def __init__(self, detail: str = "Current password is incorrect"):
        super().__init__(status_code=400, detail=detail)


class SamePasswordError(HTTPException):
    def __init__(self, detail: str = "New password must be different from the current password"):
        super().__init__(status_code=400, detail=detail)
