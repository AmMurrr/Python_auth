from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker  
import os
from dotenv import load_dotenv

load_dotenv("app/env.env")

DB_HOST_ENV = os.getenv("DB_HOST")
DB_NAME_ENV = os.getenv("DB_NAME")
DB_USER_ENV = os.getenv("DB_USER")
DB_PASSWORD_ENV = os.getenv("DB_PASSWORD")

DATABASE_URL = f"postgresql://{DB_USER_ENV}:{DB_PASSWORD_ENV}@{DB_HOST_ENV}/{DB_NAME_ENV}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))  

class LoginHistory(Base):
    __tablename__ = "login_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    login_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))  
    ip_address = Column(String, nullable=False)
    action = Column(String,nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)  




