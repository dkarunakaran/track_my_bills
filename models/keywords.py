from sqlalchemy import Column, Integer, String, ForeignKey
from .base import Base

class Keywords(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String)
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id'))
    download_method_id = Column(Integer, ForeignKey('download_methods.id'))
    sender = Column(String)
