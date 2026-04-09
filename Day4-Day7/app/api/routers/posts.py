from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.schemas import PostCreate, PostResponse, PostUpdate, CommentCreate, CommentResponse
from app.services.post_service import (
    create_post as create_post_service,
    delete_post as delete_post_service,
    get_posts as get_posts_service,
    update_post as update_post_service,
    upload_image as upload_image_service,
)
from app.services.comment_service import (
    create_comment as create_comment_service,
    delete_comment as delete_comment_service,
    get_post_comments as get_post_comments_service,
)

router = APIRouter(prefix="/api/posts", tags=["Posts"])


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    return await upload_image_service(file=file)


@router.get("/", response_model=List[PostResponse])
async def get_posts(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    return await get_posts_service(db=db, skip=skip, limit=limit)


@router.post("/", response_model=PostResponse)
async def create_post(
    post: PostCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_post_service(
        db=db,
        current_user=current_user,
        payload=post,
        background_tasks=background_tasks,
    )


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    payload: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_post_service(db=db, current_user=current_user, post_id=post_id, payload=payload)


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    return await get_post_comments_service(db=db, post_id=post_id)


@router.post("/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_comment_service(db=db, current_user=current_user, post_id=post_id, payload=payload)


@router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment(
    post_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await delete_comment_service(
        db=db,
        current_user=current_user,
        post_id=post_id,
        comment_id=comment_id,
    )


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await delete_post_service(db=db, current_user=current_user, post_id=post_id)
