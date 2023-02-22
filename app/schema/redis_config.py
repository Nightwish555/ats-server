from pydantic import validator, BaseModel

from app.schema.base import AtsModel


class RedisConfigForm(BaseModel):
    id: int = None
    name: str
    addr: str
    db: int = 0
    # username: str = ''
    password: str = ''
    cluster: bool = False
    env: int

    @validator("name", "addr", "cluster", "db", "env")
    def data_not_empty(cls, v):
        return AtsModel.not_empty(v)
