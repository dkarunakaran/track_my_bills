from sqlalchemy import Column, Integer, String
from .base import Base

class PaymentMethods(Base):
    __tablename__ = 'payment_methods'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

