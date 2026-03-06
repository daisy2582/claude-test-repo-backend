from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Post
from app.schemas import UserProfile, PostOut, PostList
from app.auth import get_current_user
from app.routers.posts import post_to_out

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
