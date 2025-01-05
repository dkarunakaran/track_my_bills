from sqlalchemy import Column, Integer, String
from .base import Base

class DownloadMethods(Base):
    __tablename__ = 'download_methods'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
