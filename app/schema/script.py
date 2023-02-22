from pydantic import BaseModel, validator

from app.schema.base import AtsModel


class PyScriptForm(BaseModel):
    command: str
    value: str

    @validator("command")
    def name_not_empty(cls, v):
        return AtsModel.not_empty(v)
