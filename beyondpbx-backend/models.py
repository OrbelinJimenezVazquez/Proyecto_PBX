from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class CDR(Base):
    __tablename__ = "cdr"
    id = Column(Integer, primary_key=True, index=True)
    src = Column(String(80))
    dst = Column(String(80))
    calldate = Column(DateTime)
    duration = Column(Integer)
    disposition = Column(String(45))