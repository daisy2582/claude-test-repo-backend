from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.database import get_db
from app.models import Comment, Post, User
from app.schemas import CommentCreate, CommentOut, UserOut
from app.auth import require_user

router = APIRouter(prefix="/api/posts/{post_id}/comments", tags=["Comments"])


def comment_to_out(comment: Comment) -> CommentOut:
    return CommentOut(
        id=comment.id,
        content=comment.content,
        created_at=comment.created_at,
        author=UserOut.model_validate(comment.author),
        parent_id=comment.parent_id,
        replies=[comment_to_out(r) for r in comment.replies] if comment.replies else [],
    )


@router.get("", response_model=list[CommentOut])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.post_id == post_id, Comment.parent_id.is_(None))
        .order_by(desc(Comment.created_at))
        .all()
    )
    return [comment_to_out(c) for c in comments]


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if data.parent_id:
        parent = db.query(Comment).filter(
            Comment.id == data.parent_id, Comment.post_id == post_id
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    comment = Comment(
        content=data.content,
        author_id=current_user.id,
        post_id=post_id,
        parent_id=data.parent_id,
    )
    db.add(comment)
    post.comment_count += 1
    db.commit()
    db.refresh(comment)

    return comment_to_out(comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    comment = db.query(Comment).filter(
        Comment.id == comment_id, Comment.post_id == post_id
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your comment")

    post = db.query(Post).filter(Post.id == post_id).first()
    if post:
        post.comment_count = max(0, post.comment_count - 1)

    db.delete(comment)
    db.commit()
