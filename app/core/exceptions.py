from fastapi.exceptions import HTTPException


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
