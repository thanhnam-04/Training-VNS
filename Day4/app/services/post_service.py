from fastapi import HTTPException, UploadFile
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import os
import time
import uuid

from app.models import Post, User
from app.schemas import PostCreate, PostUpdate


def send_email_notification(username: str, title: str):
    time.sleep(3)
    print(f"[*] Background Task: Da gui email toi {username} - Bai viet '{title}' tao thanh cong!")


async def upload_image(file: UploadFile) -> dict:
    os.makedirs("uploads", exist_ok=True)
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = f"uploads/{filename}"

    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    return {"url": f"/uploads/{filename}"}


async def get_posts(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.comments))
        .where(Post.is_published == True)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def create_post(db: AsyncSession, current_user: User, payload: PostCreate, background_tasks: BackgroundTasks):
    new_post = Post(**payload.model_dump(), owner_id=current_user.id)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    result = await db.execute(
        select(Post)
        .options(selectinload(Post.comments))
        .where(Post.id == new_post.id)
    )
    created_post = result.scalars().first()

    background_tasks.add_task(send_email_notification, current_user.username, new_post.title)
    return created_post


async def update_post(db: AsyncSession, current_user: User, post_id: int, payload: PostUpdate):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user.role != "admin" and post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)

    await db.commit()

    updated_result = await db.execute(
        select(Post)
        .options(selectinload(Post.comments))
        .where(Post.id == post_id)
    )
    return updated_result.scalars().first()


async def delete_post(db: AsyncSession, current_user: User, post_id: int):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user.role != "admin" and post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    await db.delete(post)
    await db.commit()
    return {"message": f"Post {post_id} deleted successfully"}
