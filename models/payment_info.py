from sqlalchemy import Column, Integer, String, ForeignKey
from .base import Base

class PaymentInfo(Base):
    __tablename__ = 'payment_info'
    id = Column(Integer, primary_key=True, autoincrement=True)
    details = Column(String)
    type = Column(String)
    group_id = Column(Integer, ForeignKey('group.id'))