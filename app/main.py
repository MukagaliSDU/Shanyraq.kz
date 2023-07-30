from jose import jwt

from fastapi import FastAPI, Response, Request, Form, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from pydantic import BaseModel

from .database import  SessionLocal
from .repositories.users_repository import User, UserCreate, UsersRepository, UserUpdate
from .repositories.announcement_repository import Announcement, AnnouncementsRepository, CreateAnnounce, UpdateAnnounce
from .repositories.comments_repository import CommentCreate, CommentUpdate, CommentsRepository


app = FastAPI()
oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/users/login")


#All database repository
users_repository = UsersRepository()
announce_repository = AnnouncementsRepository()
comments_repository = CommentsRepository()


class CreateAuthRequest(BaseModel):
    username: str
    phone: str
    password: str
    name: str
    city: str


class ReadUserRequest(BaseModel):
    id: str
    username: str
    phone: str
    name: str
    city: str


class UpdateUserRequest(BaseModel):
    phone: str
    name: str
    city: str


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
    db_user = users_repository.get_by_username(username=user.username,db=db)
    if db_user is not None:
        raise HTTPException(status_code=401,detail={"username": user.username, "msg": "We already have such a username."})
    user = UserCreate(username=user.username, phone=user.phone, password=user.password, name=user.name, city=user.city)
    users_repository.create_user(user=user, db=db)
    return Response(status_code=200)


@app.post("/auth/users/login",tags=["auth"] )
def post_login(username: str = Form(), password: str = Form(), db: Session = Depends(get_db)):
    db_user = users_repository.get_by_username(username=username, db=db)
    if db_user is None or db_user.password != password:
        raise HTTPException(status_code=401, detail="your username or password is incorrect")
    elif db_user.password == password:
        token = encode(str(db_user.id))
        return {
            "access_token": token,
        }


@app.get("/auth/users/me",tags=["Profile"])
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
    send_user = UserUpdate(phone=user.phone, name=user.name, city=user.city)
    users_repository.update_user(user_id=user_id, user=send_user, db=db)
    return Response(status_code=200)


@app.delete("/auth/users/me", tags=["Profile"])
def delete_user(token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    users_repository.delete_user(user_id=user_id, db=db)


class CreateAnnounceRequest(BaseModel):
    type: str
    price: int
    address: str
    area: str
    rooms_count: int
    description: str


class AnnounceResponse(BaseModel):
    id: int
    type: str
    price: int
    address: str
    area: str
    rooms_count: int
    description: str
    owner_id: int
    total_comments: int


@app.post("/shanyraks/", tags=["shanyraks"])
def post_announce(shanurak: CreateAnnounceRequest, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    new_shanurak = CreateAnnounce(
        type=shanurak.type,
        price=shanurak.price,
        address=shanurak.address,
        area=shanurak.area,
        rooms_count=shanurak.rooms_count,
        description=shanurak.description,
        owner_id=user_id
    )

    id = announce_repository.create_announce(shanyrak=new_shanurak, db=db)

    return {"id": str(id)}


@app.get("/shanyraks/{id}", tags=["shanyraks"])
def get_announce(id: int = 1, db: Session = Depends(get_db)):
    shanyrak = announce_repository.get_by_id(id=id, db=db)
    if shanyrak is None:
        raise HTTPException(status_code=404, detail={"id": id, "msg": "We have not this announcement"})
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
    db_announce = announce_repository.get_by_id(id=id, db=db)
    if db_announce.owner_id != user_id:
        raise HTTPException(status_code=405,  detail={"user_id": user_id, "msg": "You can not change this announcement"})
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
    db_announce = announce_repository.get_by_id(id=id, db=db)
    if db_announce is None:
        raise HTTPException(status_code=404, detail="Not found")
    if db_announce.owner_id != user_id:
        raise HTTPException(status_code=405,  detail={"user_id": user_id, "msg": "You can not delete this announcement"})
    announce_repository.delete_announce(id=id, db=db)
    return Response(status_code=200)


class CreateCommentRequest(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    content: str
    author_id: int
    created_at: str


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


def check_error(user_id: int, db_announce, db_comment):
    if db_announce is None:
        raise HTTPException(status_code=404, detail="Not found this Announcement")

    if db_comment is None:
        raise HTTPException(status_code=404, detail="Not found this Comment")

    if db_comment.author_id != user_id:
        raise HTTPException(status_code=405,
                            detail={"user_id": user_id, "msg": "Ooops, sory but you can't delete or update this comment"})


@app.patch("/shanyraks/{id}/comments/{comment_id}", tags=["Comments"])
def update_comment(id: int, comment_id: int, comment: CreateCommentRequest,token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = int(decode(token))
    db_announce = announce_repository.get_by_id(id=id, db=db)
    db_comment = comments_repository.get_by_comment_announce(comment_id=comment_id, announce_id=id, db=db)
    check_error(db_comment=db_comment, db_announce=db_announce, user_id=user_id)
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
    db_comment = comments_repository.get_by_comment_announce(comment_id=comment_id, announce_id=id, db=db)
    check_error(db_comment=db_comment, db_announce=db_announce, user_id=user_id)

    comments_repository.delete_comment(id=comment_id, db=db)
    return Response(status_code=200)


