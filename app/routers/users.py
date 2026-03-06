import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Post
from app.schemas import UserProfile, UserUpdate, PostOut, PostList
from app.auth import get_current_user, require_user
from app.routers.posts import post_to_out
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/{username}", response_model=UserProfile)
def get_user_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    post_count = db.query(func.count(Post.id)).filter(Post.author_id == user.id).scalar()
    total_karma = (
        db.query(func.coalesce(func.sum(Post.upvotes - Post.downvotes), 0))
        .filter(Post.author_id == user.id)
        .scalar()
    )

    return UserProfile(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url or "",
        bio=user.bio or "",
        created_at=user.created_at,
        post_count=post_count,
        total_karma=total_karma,
    )


@router.put("/me", response_model=UserProfile)
def update_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if data.display_name is not None:
        current_user.display_name = data.display_name
    if data.bio is not None:
        current_user.bio = data.bio
    db.commit()
    db.refresh(current_user)

    post_count = db.query(func.count(Post.id)).filter(Post.author_id == current_user.id).scalar()
    total_karma = (
        db.query(func.coalesce(func.sum(Post.upvotes - Post.downvotes), 0))
        .filter(Post.author_id == current_user.id)
        .scalar()
    )

    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url or "",
        bio=current_user.bio or "",
        created_at=current_user.created_at,
        post_count=post_count,
        total_karma=total_karma,
    )


@router.post("/me/avatar", response_model=UserProfile)
async def upload_avatar(
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    allowed = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if avatar.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Invalid image type")

    os.makedirs(os.path.join(settings.upload_dir, "avatars"), exist_ok=True)
    ext = avatar.filename.rsplit(".", 1)[-1] if "." in avatar.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(settings.upload_dir, "avatars", filename)

    file_content = await avatar.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB.")

    with open(filepath, "wb") as f:
        f.write(file_content)

    current_user.avatar_url = f"/uploads/avatars/{filename}"
    db.commit()
    db.refresh(current_user)

    post_count = db.query(func.count(Post.id)).filter(Post.author_id == current_user.id).scalar()
    total_karma = (
        db.query(func.coalesce(func.sum(Post.upvotes - Post.downvotes), 0))
        .filter(Post.author_id == current_user.id)
        .scalar()
    )

    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url or "",
        bio=current_user.bio or "",
        created_at=current_user.created_at,
        post_count=post_count,
        total_karma=total_karma,
    )


@router.get("/{username}/posts", response_model=list[PostOut])
def get_user_posts(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    posts = (
        db.query(Post)
        .filter(Post.author_id == user.id)
        .order_by(Post.created_at.desc())
        .all()
    )
    return [post_to_out(p, current_user) for p in posts]
