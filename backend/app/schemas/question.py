from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=10)
    chat_id: int | None = Field(default=None, gt=0)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be empty.")
        return value


class CodeSnippet(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    language: str
    code: str


class Reference(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    reason: str


class Source(BaseModel):
    chunk_id: str
    file_path: str
    score: float


class AskResponse(BaseModel):
    chat_id: int
    question: str
    answer: str
    code_snippets: list[CodeSnippet]
    references: list[Reference]
    sources: list[Source]
