from pydantic import validator, BaseModel

from app.schema.base import AtsModel


class DatabaseForm(BaseModel):
    id: int = None
    name: str
    host: str
    port: int = None
    username: str
    password: str
    database: str
    sql_type: int
    env: int

    @validator("name", "host", "port", "username", "password", "database", "sql_type", "env")
    def data_not_empty(cls, v):
        return AtsModel.not_empty(v)
