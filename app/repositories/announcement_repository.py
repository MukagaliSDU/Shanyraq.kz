from typing import List, Type

from attr import define
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, desc
from sqlalchemy.orm import relationship, Session

from ..database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    price = Column(Integer)
    address = Column(String)
    area = Column(String)
    rooms_count = Column(Integer)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="announcements")
    comments = relationship("Comment", back_populates="announce")
    favorites = relationship('Favorites', back_populates="announcements", cascade="all, delete")

@define
class CreateAnnounce:
    type: str
    price: int
    address: str
    area: str
    rooms_count: int
    description: str
    owner_id: int


@define
class UpdateAnnounce:
    type: str
    price: int
    address: str
    area: str
    rooms_count: int
    description: str


class AnnouncementsRepository:

    def create_announce(self, shanyrak: CreateAnnounce, db: Session) -> int:
        db_announce = Announcement(
            type=shanyrak.type,
            price=shanyrak.price,
            address=shanyrak.address,
            area=shanyrak.area,
            rooms_count=shanyrak.rooms_count,
            description=shanyrak.description,
            owner_id=shanyrak.owner_id
        )
        db.add(db_announce)
        db.commit()
        db.refresh(db_announce)
        return db_announce.id

    def search_announce(self, db: Session, limit: int = 10, offset: int = 0,
                        _type: str = None, rooms_count: int = None,
                        price_from: int = None, price_until: int = None):
        filters = []
        if _type is not None:
            filters.append(Announcement.type == _type)
        if rooms_count is not None:
            filters.append(Announcement.rooms_count == int(rooms_count))
        if price_from is not None:
            filters.append(Announcement.price >= price_from)
        if price_until is not None:
            filters.append(Announcement.price <= price_until)
        query = db.query(Announcement)
        if filters:
            query = query.filter(*filters)
        total = query.count()
        query = query.order_by(desc(Announcement.id)).limit(limit).offset(offset).all()
        return {"total": total, "query": query}
    
    def get_by_id(self, id: int, db: Session) -> Announcement:
        return db.query(Announcement).filter(Announcement.id==id).first()

    def update_announce(self, id: int, shanyrak: UpdateAnnounce, db: Session):
        db_announce = self.get_by_id(id=id, db=db)
        db_announce.type = shanyrak.type
        db_announce.price = shanyrak.price
        db_announce.address = shanyrak.address
        db_announce.area = shanyrak.area
        db_announce.rooms_count = shanyrak.rooms_count
        db_announce.description = shanyrak.description

        db.commit()
        db.refresh(db_announce)
        return db_announce

    def delete_announce(self, id: int, db: Session):
            db_announce = self.get_by_id(id=id, db=db)
            db.delete(db_announce)
            db.commit()

    
