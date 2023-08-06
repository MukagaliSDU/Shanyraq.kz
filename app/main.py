from jose import jwt

from fastapi import FastAPI, Response, Request, Form, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from pydantic import BaseModel

from .database import SessionLocal
from .repositories.users_repository import User, UserCreate, UsersRepository, UserUpdate
from .repositories.announcement_repository import Announcement, AnnouncementsRepository, CreateAnnounce, UpdateAnnounce
from .repositories.comments_repository import Comment, CommentCreate, CommentUpdate, CommentsRepository
from .repositories.favorites_repository import Favorites, CreateFavorites, FavoriteRepositories

# models
from .models.users_models import CreateAuthRequest, ReadUserRequest, UpdateUserRequest
from .models.announcement_models import CreateAnnounceRequest, AnnounceResponse, AnnounceResponseFilter
from .models.comments_models import CommentResponse, CreateCommentRequest


app = FastAPI()
oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/users/login")


# All database repository
users_repository = UsersRepository()
announce_repository = AnnouncementsRepository()
comments_repository = CommentsRepository()
favorites_repository = FavoriteRepositories()

def encode(user_id: str) -> str:
    json_user = {"user_id": user_id}
    token = jwt.encode(json_user, "bereke", "HS256")
    return token


def decode(token: str) -> int:
    data = jwt.decode(token, "bereke", "HS256")
    return data["user_id"]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root(request: Request):
    pass


@app.post("/auth/users/", tags=["auth"])
def post_register(user: CreateAuthRequest, db: Session = Depends(get_db)):
    db_user = users_repository.get_by_username(username=user.username, db=db)
    if db_user is not None:
        raise HTTPException(status_code=401, detail={"username": user.username, "msg": "We already have such a username."})
    user_db = UserCreate(**user.dict())
    users_repository.create_user(user=user_db, db=db)
    return Response(status_code=200)


@app.post("/auth/users/login", tags=["auth"])
def post_login(username: str = Form(), password: str = Form(), db: Session = Depends(get_db)):
    db_user = users_repository.get_by_username(username=username, db=db)
    if db_user is None or db_user.password != password:
        raise HTTPException(status_code=401, detail="your username or password is incorrect")
    elif db_user.password == password:
        token = encode(str(db_user.id))
        return {
            "access_token": token,
        }


@app.get("/auth/users/me", tags=["Profile"])
def get_profile(token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    db_user = users_repository.get_by_id(user_id=user_id, db=db)
    if db_user is None:
        raise HTTPException(status_code=401, detail={"user_id": user_id, "msg": "this users not found"})

    user = ReadUserRequest(id=user_id, username=db_user.username, phone=db_user.phone, name=db_user.name, city=db_user.city)
    return user


@app.patch("/auth/users/me", tags=["Profile"])
def update_user(user: UpdateUserRequest, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail={"user_id": user_id, "msg": "this users not found"})
    send_user = UserUpdate(**user.dict())
    users_repository.update_user(user_id=user_id, user=send_user, db=db)
    return Response(status_code=200)


@app.delete("/auth/users/me", tags=["Profile"])
def delete_user(token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    users_repository.delete_user(user_id=user_id, db=db)


@app.post("/shanyraks/", tags=["shanyraks"])
def post_announce(shanyrak: CreateAnnounceRequest, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    new_shanyrak = CreateAnnounce(**shanyrak.dict(), owner_id=user_id)

    id = announce_repository.create_announce(shanyrak=new_shanyrak, db=db)
    return {"id": str(id)}


# this method return the announcement in database if is not exist then return exception
def get_announce(id: int, db: Session = Depends(get_db)):
    shanyrak = announce_repository.get_by_id(id=id, db=db)
    if shanyrak is None:
        raise HTTPException(status_code=404, detail={"id": id, "msg": "Oops, but there are no such announcement"})
    return shanyrak


@app.get("/shanyraks/{id}", tags=["shanyraks"])
def get_shanyraks(id: int = 1, db: Session = Depends(get_db)):
    shanyrak = get_announce(id=id, db=db)
    total = len(comments_repository.get_by_announce_id(announce_id=id, db=db))
    response_shanyrak = AnnounceResponse(
        id=shanyrak.id,
        type=shanyrak.type,
        price=shanyrak.price,
        address=shanyrak.address,
        area=shanyrak.area,
        rooms_count=shanyrak.rooms_count,
        description=shanyrak.description,
        owner_id=shanyrak.owner_id,
        total_comments=total
    )
    return response_shanyrak


@app.patch("/shanyraks/{id}", tags=["shanyraks"])
def update_announce(shanyrak: CreateAnnounceRequest, id: int, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = int(decode(token))
    db_announce = get_announce(id=id, db=db)
    if db_announce.owner_id != user_id:
        raise HTTPException(status_code=403,  detail={"user_id": user_id, "msg": "You can not change this announcement"})
    announce = UpdateAnnounce(
        type=shanyrak.type,
        price=shanyrak.price,
        address=shanyrak.address,
        area=shanyrak.area,
        rooms_count=shanyrak.rooms_count,
        description=shanyrak.description,
    )
    announce_repository.update_announce(id=id, shanyrak=announce, db=db)
    return Response(status_code=200)


@app.delete("/shanyraks/{id}", tags=["shanyraks"])
def delete_announce(id: int, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = int(decode(token))
    db_announce = get_announce(id=id, db=db)
    if db_announce.owner_id != user_id:
        raise HTTPException(status_code=403,  detail={"user_id": user_id, "msg": "You can not delete this announcement"})
    announce_repository.delete_announce(id=id, db=db)
    return Response(status_code=200)


@app.post("/shanyraks/{id}/comments", tags=["Comments"])
def post_comment(id: int, comment: CreateCommentRequest, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
        user_id = decode(token)
        db_announce = announce_repository.get_by_id(id=id, db=db)
        if db_announce is None:
            raise HTTPException(status_code=404, detail="Not found this Announcement")
        request_comment = CommentCreate(
            content=comment.content,
            author_id=user_id,
            announce_id=id
        )
        comments_repository.create_comment(comment=request_comment, db=db)
        return Response(status_code=200)


@app.get("/shanyraks/{id}/comments", tags=["Comments"])
def get_comments(id: int, db: Session = Depends(get_db)):
    db_announce = announce_repository.get_by_id(id=id, db=db)
    if db_announce is None:
        raise HTTPException(status_code=404, detail="Not found this Announcement")
    comments = comments_repository.get_by_announce_id(announce_id=id, db=db)
    response_comments = []
    for comment in comments:
        temp = CommentResponse(id=comment.id, content=comment.content, author_id=comment.author_id, created_at=comment.created_at)
        response_comments.append(temp)
    return {"comments": response_comments}


def is_exist_comment_announce(db_announce: Announcement, db_comment: Comment):
    if db_announce is None:
        raise HTTPException(status_code=404, detail="Not found this Announcement")

    if db_comment is None:
        raise HTTPException(status_code=404, detail="Not found this Comment")


@app.patch("/shanyraks/{id}/comments/{comment_id}", tags=["Comments"])
def update_comment(id: int, comment_id: int, comment: CreateCommentRequest, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = int(decode(token))
    db_announce = announce_repository.get_by_id(id=id, db=db)
    db_comment = comments_repository.get_comment_by_announce(comment_id=comment_id, announce_id=id, db=db)
    is_exist_comment_announce(db_announce=db_announce, db_comment=db_comment)

    if db_comment.author_id != user_id:
        raise HTTPException(status_code=405, detail={"user_id": user_id, "msg": "Ooops, sory but you can't update this comment"})

    new_comment = CommentUpdate(content=comment.content)
    comments_repository.update_comment(comment_id=comment_id, new_comment=new_comment, db=db)
    return Response(status_code=200)


@app.delete("/shanyraks/{id}/comments/{comment_id}", tags=["Comments"])
def update_comment(
        id: int,
        comment_id: int,
        token: str = Depends(oauth2_schema),
        db: Session = Depends(get_db)
):
    user_id = int(decode(token))
    db_announce = announce_repository.get_by_id(id=id, db=db)
    db_comment = comments_repository.get_comment_by_announce(comment_id=comment_id, announce_id=id, db=db)
    is_exist_comment_announce(db_announce=db_announce, db_comment=db_comment)

    if db_announce.owner_id == user_id or db_comment.author_id == user_id:
        comments_repository.delete_comment(id=comment_id, db=db)
    else:
        raise HTTPException(status_code=403, detail={"user_id": user_id, "msg": "Bearer <token not author>"})
    return Response(status_code=200)


@app.post("/auth/users/favorites/shanyraks/{id}", tags=["Favorites"])
def post_favorites(id: int, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    db_announce = announce_repository.get_by_id(id=id, db=db)
    if db_announce is None:
        raise HTTPException(status_code=404, detail="Ooops, we haven't this shanyraq")
    add = CreateFavorites(user_id=user_id, announcement_id=id, address=db_announce.address)
    favorites_repository.create_favorites(favorites=add, db=db)
    return Response(status_code=200)


@app.get("/auth/users/favorites/shanyraks", tags=["Favorites"])
def get_favorites(token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    favorites = favorites_repository.get_response_favorites(user_id=user_id, db=db)
    for i in favorites:
        i.address = announce_repository.get_by_id(id=i.id, db=db).address
    return {"shanyraks": favorites}


@app.delete("/auth/users/favorites/shanyraks/{id}", tags=["Favorites"])
def delete_favorites(id: int, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    db_favorites = favorites_repository.get_by_announce_id(id=id, db=db)
    if db_favorites is None:
        raise HTTPException(status_code=404, detail="Ooops, sorry but you don't have such favorites")
    favorites_repository.delete_favorites(shanyrak_id=id, user_id=user_id, db=db)
    return Response(status_code=200)


def change_response(data: list[Announcement]) -> list[AnnounceResponseFilter]:
    res = []
    if data is None:
        print("wiqwrieqwe")
        return res
    for announcement in data:
        new_model = AnnounceResponseFilter(
            id=announcement.id,
            type=announcement.type,
            price=announcement.price,
            address=announcement.address,
            area=announcement.area,
            rooms_count=announcement.rooms_count
        )
        res.append(new_model)
    return res


@app.get("/shanyraks", tags=["Filter"])
def get_announcements(limit: int = 10, offset: int = 0,
                      _type: str = None, rooms_count: int = None,
                      price_from: int = None, price_until: int = None,
                      db: Session = Depends(get_db)):
    announcements = announce_repository.search_announce(limit=limit, offset=offset,
                                         _type=_type, rooms_count=rooms_count,
                                         price_from=price_from, price_until=price_until, db=db)
    res = change_response(data=announcements["query"])
    return {
        "total": announcements['total'],
        "announcement": res
    }