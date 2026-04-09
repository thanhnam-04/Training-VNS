import os
import time
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.post import Comment, Post
from app.schemas import CommentCreate, CommentResponse, CurrentUser, PostCreate, PostResponse, PostUpdate

router = APIRouter(prefix="/api/posts", tags=["Posts"])


def send_email_notification(username: str, title: str):
    time.sleep(2)
    print(f"[*] Background Task: notified {username} for post '{title}'")


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), _: CurrentUser = Depends(get_current_user)):
    os.makedirs("uploads", exist_ok=True)
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = f"uploads/{filename}"

    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    return {"url": f"/uploads/{filename}"}


@router.get("/", response_model=List[PostResponse])
async def get_posts(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.comments))
        .where(Post.is_published == True)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/", response_model=PostResponse)
async def create_post(
    post: PostCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    new_post = Post(**post.model_dump(), owner_id=current_user.id)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    result = await db.execute(
        select(Post).options(selectinload(Post.comments)).where(Post.id == new_post.id)
    )
    created_post = result.scalars().first()
    background_tasks.add_task(send_email_notification, current_user.username, new_post.title)
    return created_post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    payload: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user.role != "admin" and post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(post, key, value)

    await db.commit()

    updated_result = await db.execute(
        select(Post).options(selectinload(Post.comments)).where(Post.id == post_id)
    )
    return updated_result.scalars().first()


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user.role != "admin" and post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    await db.delete(post)
    await db.commit()
    return {"message": f"Post {post_id} deleted successfully"}


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    if not post_result.scalars().first():
        raise HTTPException(status_code=404, detail="Post not found")

    result = await db.execute(select(Comment).where(Comment.post_id == post_id).order_by(Comment.id.asc()))
    return result.scalars().all()


@router.post("/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    if not post_result.scalars().first():
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = Comment(content=payload.content, post_id=post_id, author_id=current_user.id)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment


@router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment(
    post_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    if not post_result.scalars().first():
        raise HTTPException(status_code=404, detail="Post not found")

    comment_result = await db.execute(select(Comment).where(Comment.id == comment_id, Comment.post_id == post_id))
    comment = comment_result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if current_user.role != "admin" and comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    await db.delete(comment)
    await db.commit()
    return {"message": f"Comment {comment_id} deleted successfully"}
