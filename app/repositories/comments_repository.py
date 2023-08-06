import datetime

from attr import define
from sqlalchemy import  Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Session

from ..database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    created_at = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    announce_id = Column(Integer, ForeignKey("announcements.id"))

    parent = relationship("User", back_populates="comments")
    announce = relationship("Announcement", back_populates="comments")


@define
class CommentCreate:
    content: str
    author_id: int
    announce_id: int
    created_at: str = datetime.datetime.now()


@define
class CommentUpdate:
    content: str
    created_at: str = datetime.datetime.now()


class CommentsRepository:

    def create_comment(self, comment: CommentCreate, db: Session) -> Comment:
        db_comment = Comment(
            content=comment.content,
            created_at=comment.created_at,
            author_id=comment.author_id,
            announce_id=comment.announce_id
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return db_comment

    def get_by_id(self, id: int, db: Session) -> Comment:
        return db.query(Comment).filter(Comment.id==id).first()

    def get_comment_by_announce(self, comment_id: int, announce_id: int, db: Session):
        return db.query(Comment).filter(Comment.id==comment_id, Comment.announce_id==announce_id).first()

    def get_by_announce_id(self, announce_id: int, db: Session):
        return db.query(Comment).filter(Comment.announce_id==announce_id).all()

    def delete_comment(self, id: int, db: Session):
        db_comment = self.get_by_id(id=id, db=db)
        db.delete(db_comment)
        db.commit()

    def update_comment(self, comment_id: int, new_comment: CommentUpdate, db: Session) -> Comment:
        db_comment = self.get_by_id(id=comment_id, db=db)
        db_comment.content = new_comment.content
        db_comment.created_at = new_comment.created_at

        db.commit()
        db.refresh(db_comment)
        return db_comment



