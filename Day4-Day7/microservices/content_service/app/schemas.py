from typing import List, Optional
from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: int
    username: str
    role: str


class PostCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    is_published: Optional[bool] = False


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    is_published: Optional[bool] = None


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    content: str
    post_id: int
    author_id: int

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    image_url: Optional[str] = None
    is_published: bool
    owner_id: int
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True
