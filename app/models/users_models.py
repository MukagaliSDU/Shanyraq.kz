from pydantic import BaseModel


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

