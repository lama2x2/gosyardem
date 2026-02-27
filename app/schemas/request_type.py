from pydantic import BaseModel, ConfigDict


class RequestTypeBase(BaseModel):
    name: str
    slug: str


class RequestTypeCreate(RequestTypeBase):
    pass


class RequestTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
