import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from typing import Optional
from app.database import get_db
from app.models import Post, PostCategory, User, Vote, Comment
from app.schemas import PostCreate, PostUpdate, PostOut, PostList, UserOut, VoteCreate
from app.auth import get_current_user, require_user
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/posts", tags=["Posts"])


def post_to_out(post: Post, current_user: Optional[User] = None) -> PostOut:
    user_vote = None
    if current_user:
        vote = next((v for v in post.votes if v.user_id == current_user.id), None)
        if vote:
            user_vote = vote.value
    return PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        category=post.category,
        image_url=post.image_url or "",
        upvotes=post.upvotes,
        downvotes=post.downvotes,
        comment_count=post.comment_count,
        is_pinned=post.is_pinned,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=UserOut.model_validate(post.author),
        user_vote=user_vote,
    )


@router.get("", response_model=PostList)
def list_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[PostCategory] = None,
    sort: str = Query("new", regex="^(new|top|hot)$"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    query = db.query(Post).options(joinedload(Post.author), joinedload(Post.votes))

    if category:
        query = query.filter(Post.category == category)
    if search:
        query = query.filter(
            Post.title.ilike(f"%{search}%") | Post.content.ilike(f"%{search}%")
        )

    total = query.count()

    if sort == "top":
        query = query.order_by(desc(Post.upvotes - Post.downvotes))
    elif sort == "hot":
        query = query.order_by(desc(Post.comment_count), desc(Post.created_at))
    else:
        query = query.order_by(desc(Post.is_pinned), desc(Post.created_at))

    posts = query.offset((page - 1) * per_page).limit(per_page).all()

    return PostList(
        posts=[post_to_out(p, current_user) for p in posts],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    category: PostCategory = Form(PostCategory.DISCUSSION),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    image_url = ""
    if image and image.filename:
        # Validate file type
        allowed = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        if image.content_type not in allowed:
            raise HTTPException(status_code=400, detail="Invalid image type. Use JPEG, PNG, GIF, or WebP.")

        # Save file
        os.makedirs(settings.upload_dir, exist_ok=True)
        ext = image.filename.rsplit(".", 1)[-1] if "." in image.filename else "jpg"
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(settings.upload_dir, filename)

        file_content = await image.read()
        if len(file_content) > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File too large. Max {settings.max_file_size_mb}MB.")

        with open(filepath, "wb") as f:
            f.write(file_content)
        image_url = f"/uploads/{filename}"

    post = Post(
        title=title,
        content=content,
        category=category,
        image_url=image_url,
        author_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return post_to_out(post, current_user)


@router.get("/{post_id}", response_model=PostOut)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    post = (
        db.query(Post)
        .options(joinedload(Post.author), joinedload(Post.votes))
        .filter(Post.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post_to_out(post, current_user)


@router.put("/{post_id}", response_model=PostOut)
def update_post(
    post_id: int,
    data: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post_to_out(post, current_user)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")
    db.delete(post)
    db.commit()


@router.post("/{post_id}/vote", response_model=PostOut)
def vote_post(
    post_id: int,
    data: VoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    post = (
        db.query(Post)
        .options(joinedload(Post.author), joinedload(Post.votes))
        .filter(Post.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = db.query(Vote).filter(
        Vote.user_id == current_user.id, Vote.post_id == post_id
    ).first()

    if data.value == 0:
        # Remove vote
        if existing:
            if existing.value == 1:
                post.upvotes = max(0, post.upvotes - 1)
            else:
                post.downvotes = max(0, post.downvotes - 1)
            db.delete(existing)
    elif existing:
        # Change vote
        if existing.value != data.value:
            if data.value == 1:
                post.upvotes += 1
                post.downvotes = max(0, post.downvotes - 1)
            else:
                post.downvotes += 1
                post.upvotes = max(0, post.upvotes - 1)
            existing.value = data.value
    else:
        # New vote
        vote = Vote(user_id=current_user.id, post_id=post_id, value=data.value)
        db.add(vote)
        if data.value == 1:
            post.upvotes += 1
        else:
            post.downvotes += 1

    db.commit()
    db.refresh(post)
    return post_to_out(post, current_user)
