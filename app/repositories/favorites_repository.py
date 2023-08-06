from attr import define
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Session

from ..database import Base

from ..models.favorites_models import FavoritesResponse


class Favorites(Base):
    __tablename__ = "faborites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    announcement_id = Column(Integer, ForeignKey("announcements.id", ondelete="CASCADE"))
    address = Column(String)

    owner = relationship("User", back_populates="favorites")
    announcements = relationship("Announcement", back_populates="favorites")


@define
class CreateFavorites:
    user_id: int
    announcement_id: int
    address: str


class FavoriteRepositories:
    def create_favorites(self, favorites: CreateFavorites, db: Session) -> Favorites:
        db_favorites = Favorites(user_id=favorites.user_id, announcement_id=favorites.announcement_id, address=favorites.address)
        db.add(db_favorites)
        db.commit()
        db.refresh(db_favorites)
        return db_favorites

    def get_favorites(self, user_id: int, db: Session) -> list[Favorites]:
        return db.query(Favorites).filter(Favorites.user_id == user_id).all()

    def get_by_id(self, id: int, db: Session) -> Favorites:
        return db.query(Favorites).filter(Favorites.id==id).first()

    def get_by_announce_id(self, id: int, db: Session) -> Favorites:
        return db.query(Favorites).filter(Favorites.announcement_id==id).first()

    def get_response_favorites(self, user_id: int, db: Session) -> list[FavoritesResponse]:
        db_list_favorites = self.get_favorites(user_id=user_id, db=db)
        if db_list_favorites is None:
            return []
        res = []
        for favorites in db_list_favorites:
            res.append(FavoritesResponse(id=favorites.announcement_id, address=favorites.address))
        return res

    def delete_favorites(self, shanyrak_id: int, user_id: int, db: Session):
        db_favorites = db.query(Favorites).filter(Favorites.announcement_id==shanyrak_id, Favorites.user_id==user_id).first()
        db.delete(db_favorites)
        db.commit()