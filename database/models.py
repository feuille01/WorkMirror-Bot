from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text
)
from sqlalchemy.orm import declarative_base, relationship
import datetime


Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    company_code = Column(String, unique=True, nullable=False)
    company_name = Column(String, nullable=True)

    questions = relationship("Question", back_populates="company")
    access_codes = relationship("AccessCode", back_populates="company")

class AccessCode(Base):
    __tablename__ = "access_codes"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    access_code = Column(String, nullable=False)

    company = relationship("Company", back_populates="access_codes")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    question_text = Column(Text, nullable=False)

    # Для валидации
    question_type = Column(String, nullable=True)     # "yes_no", "numeric", "open_text"
    constraints   = Column(Text, nullable=True)       # JSON string, {"min_value": 0, "max_value": 10}

    company = relationship("Company", back_populates="questions")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_id = Column(String, nullable=True)
    answer_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)

class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    analysis_result = Column(Text, nullable=True)  # место хранения JSON ответа от YandexGPT