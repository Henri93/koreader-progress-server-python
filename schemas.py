from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class ProgressUpdate(BaseModel):
    document: str
    progress: str
    percentage: float
    device: str
    device_id: str


class ProgressResponse(BaseModel):
    document: str
    progress: str
    percentage: float
    device: str
    device_id: str
    timestamp: int
