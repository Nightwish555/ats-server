from pydantic import BaseModel, validator


class WechatForm(BaseModel):
    signature: str
    timestamp: int
    nonce: str
    echostr: str
