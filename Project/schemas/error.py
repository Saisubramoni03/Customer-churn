from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    status_code: int