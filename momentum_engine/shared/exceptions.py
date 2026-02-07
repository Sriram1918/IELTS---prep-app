"""Shared exceptions for the Momentum Engine."""


class MomentumEngineException(Exception):
    """Base exception for all application errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error_code: str = "INTERNAL_ERROR"
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class NotFoundError(MomentumEngineException):
    """Resource not found."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with ID '{identifier}' not found",
            status_code=404,
            error_code="NOT_FOUND"
        )


class ValidationError(MomentumEngineException):
    """Validation failed."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR"
        )


class BudgetExceededError(MomentumEngineException):
    """AI budget exceeded."""
    
    def __init__(self, user_id: str):
        super().__init__(
            message=f"AI budget exceeded for user {user_id}",
            status_code=429,
            error_code="BUDGET_EXCEEDED"
        )


class RateLimitError(MomentumEngineException):
    """Rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT"
        )


class AIError(MomentumEngineException):
    """AI service error."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=503,
            error_code="AI_ERROR"
        )
