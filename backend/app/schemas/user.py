from pydantic import BaseModel

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True
