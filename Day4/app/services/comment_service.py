from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Post, User, Comment
from app.schemas import CommentCreate


async def get_post_comments(db: AsyncSession, post_id: int):
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    post = post_result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    result = await db.execute(select(Comment).where(Comment.post_id == post_id).order_by(Comment.id.asc()))
    return result.scalars().all()


async def create_comment(db: AsyncSession, current_user: User, post_id: int, payload: CommentCreate):
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    post = post_result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = Comment(content=payload.content, post_id=post_id, author_id=current_user.id)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment


async def delete_comment(db: AsyncSession, current_user: User, post_id: int, comment_id: int):
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    post = post_result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment_result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.post_id == post_id)
    )
    comment = comment_result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if current_user.role != "admin" and comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    await db.delete(comment)
    await db.commit()
    return {"message": f"Comment {comment_id} deleted successfully"}
