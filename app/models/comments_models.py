from pydantic import BaseModel


class CreateCommentRequest(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    content: str
    author_id: int
    created_at: str