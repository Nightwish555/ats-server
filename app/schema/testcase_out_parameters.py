from pydantic import BaseModel, validator

from app.schema.base import AtsModel


class TestCaseOutParametersForm(BaseModel):
    id: int = None
    # case_id = None
    name: str
    expression: str = None
    match_index: str = None
    source: int

    @validator("name", "source")
    def name_not_empty(cls, v):
        return AtsModel.not_empty(v)


class PityTestCaseParametersDto(TestCaseOutParametersForm):
    case_id: int = None


class PityTestCaseVariablesDto(BaseModel):
    case_id: int
    step_name: str