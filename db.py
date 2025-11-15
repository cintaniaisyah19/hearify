from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Song(Base):
    __tablename__ = 'songs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(300))
    artist = Column(String(300))
    lyrics = Column(Text)
    url = Column(String(500))


DATABASE_URL = 'sqlite:///hearify.db'

def init_db():
    # Buat engine dan session
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session  # ✅ Ini penting!
