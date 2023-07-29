from attr import define
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Session

from ..database import Base
from .announcement_repository import Announcement

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    phone = Column(String)
    password = Column(String)
    name = Column(String)
    city = Column(String)

    announcements = relationship("Announcement", back_populates="owner")
    comments = relationship("Comment", back_populates="parent")


@define
class UserCreate:
    username: str
    phone: str
    password: str
    name: str
    city: str


@define
class UserUpdate:
    phone: str
    name: str
    city: str


class UsersRepository:

    def create_user(self, user: UserCreate, db: Session) -> User:
        db_user = User(username=user.username, phone=user.phone, password=user.password, name=user.name, city=user.city)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get_by_username(self, username: str, db: Session):
        return db.query(User).filter(User.username  == username).first()

    def get_by_id(self, user_id: int, db: Session) -> User:
        return db.query(User).filter(User.id==user_id).first()

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def delete_user(self, user_id: int, db: Session):
        db_user = self.get_by_id(user_id=user_id,db=db)
        db.delete(db_user)
        db.commit()


    def update_user(self, user_id: int, user: UserUpdate, db: Session):
        db_user = self.get_by_id(user_id=user_id, db=db)
        db_user.phone = user.phone
        db_user.name = user.name
        db_user.city = user.city

        db.commit()
        db.refresh(db_user)
        return db_user

