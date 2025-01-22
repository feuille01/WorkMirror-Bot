from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_PATH
from .models import Base

engine = create_engine(DB_PATH, echo=False)

# Создаём таблицы (если они ещё не созданы)
Base.metadata.create_all(engine)

# Создание сессий
SessionLocal = sessionmaker(bind=engine)