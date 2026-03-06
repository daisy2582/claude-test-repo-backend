from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.models import PostCategory


# ---- Auth / User ----

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    avatar_url: str = ""
    bio: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfile(UserOut):
    post_count: int = 0
    total_karma: int = 0


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- Posts ----

class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1)
    category: PostCategory = PostCategory.DISCUSSION


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[PostCategory] = None


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    category: PostCategory
    image_url: str = ""
    upvotes: int = 0
    downvotes: int = 0
    comment_count: int = 0
    is_pinned: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    author: UserOut
    user_vote: Optional[int] = None  # +1, -1, or None

    model_config = {"from_attributes": True}


class PostList(BaseModel):
    posts: list[PostOut]
    total: int
    page: int
    per_page: int
    has_more: bool


# ---- Comments ----

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)
    parent_id: Optional[int] = None


class CommentOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    author: UserOut
    parent_id: Optional[int] = None
    replies: list["CommentOut"] = []

    model_config = {"from_attributes": True}


# ---- Votes ----

class VoteCreate(BaseModel):
    value: int = Field(..., ge=-1, le=1)  # -1, 0 (remove), or +1
