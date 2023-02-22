from pydantic import BaseModel, validator

from app.schema.base import AtsModel


class OnlineSQLForm(BaseModel):
    id: int = None
    sql: str

    @validator("sql", 'id')
    def name_not_empty(cls, v):
        return AtsModel.not_empty(v)
