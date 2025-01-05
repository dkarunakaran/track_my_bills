# models/content.py
from sqlalchemy import Column, Integer, String
from .base import Base

class Content(Base):
    __tablename__ = 'content'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    date = Column(String)
    amount = Column(String)
    payment = Column(String)
    processed = Column(String)
    paid = Column(Integer, default=0)
    created_date = Column(String)
