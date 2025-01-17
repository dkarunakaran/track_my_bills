from sqlalchemy import Column, Integer, String
from .base import Base

class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
