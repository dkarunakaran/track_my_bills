from sqlalchemy import Column, Integer, String, ForeignKey
from .base import Base

class DifferentName(Base):
    __tablename__ = 'different_name'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    group_id = Column(Integer, ForeignKey('group.id'))