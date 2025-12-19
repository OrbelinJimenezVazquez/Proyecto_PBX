from pydantic import BaseModel
from datetime import datetime

class CDRResponse(BaseModel):
    id: int
    src: str
    dst: str
    calldate: datetime
    duration: int
    disposition: str

    class Config:
        from_attributes = True