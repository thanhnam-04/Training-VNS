from pydantic import BaseModel
from typing import Optional, List

from app.schemas.comment import CommentResponse


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
