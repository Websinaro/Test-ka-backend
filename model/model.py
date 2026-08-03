from sqlalchemy import Column,Integer,String
from database.database import Base

class User(Base):
	__tablename__ = "users"
	
	id = Column(Integer,primary_key=True,index=True)
	name = Column(String(100),nullable=False)
	email = Column(String(150),unique=True,nullable=False)
	phone = Column(String(20),nullable=False)
	password = Column(String(255),nullable=False)
	district = Column(String(50),nullable=False)
	role = Column(String(40),default="user",nullable=False)
	created_time = Column(String(50),nullable=False)