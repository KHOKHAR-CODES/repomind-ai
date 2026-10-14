from pydantic import BaseModel

class ChatOut(BaseModel):
    id: int
    repository_id: int
    title: str

    class Config:
        from_attributes = True

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    source_metadata: str | None

    class Config:
        from_attributes = True
