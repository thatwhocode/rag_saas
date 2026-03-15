class AuthError(Exception):
    def __init__(self, message: str):
        self.message = message

class UserAlreadyExistsError(AuthError):
    pass

class InvalidCredentialsError(AuthError):
    pass

class TokenError(AuthError):
    pass

class UsernameAlreadyInUse(AuthError):
    pass
class AccessDeniedException(AuthError):
    pass