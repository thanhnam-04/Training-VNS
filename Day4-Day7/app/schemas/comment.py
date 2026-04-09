from pydantic import BaseModel


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    content: str
    post_id: int
    author_id: int

    class Config:
        from_attributes = True
