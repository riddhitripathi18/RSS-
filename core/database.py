"""
Database setup and models for RSS News Digest System
"""
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean, inspect, text
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.declarative import declarative_base
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from core.config import DATABASE_URL
import hashlib

Base = declarative_base()

class Article(Base):
    """Model for storing news articles"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    content = Column(Text)
    source = Column(String)
    published_date = Column(DateTime)
    fetched_date = Column(DateTime, default=datetime.utcnow)
    url_hash = Column(String, unique=True)  # For duplicate detection
    is_duplicate = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    is_digested = Column(Boolean, default=False)  # True once included in a digest
    click_count = Column(Integer, default=0)      # Click tracking count
    
    def __repr__(self):
        return f"<Article(title='{self.title}', source='{self.source}')>"
    
    def set_url_hash(self):
        """Generate hash of URL for duplicate detection"""
        self.url_hash = hashlib.md5(self.url.encode()).hexdigest()



class Digest(Base):
    """Model for storing daily digests"""
    __tablename__ = "digests"
    
    id = Column(Integer, primary_key=True)
    digest_date = Column(DateTime, default=datetime.utcnow)
    content = Column(Text)
    article_count = Column(Integer)
    is_sent = Column(Boolean, default=False)
    sent_date = Column(DateTime)


# Database setup functions
def init_db():
    """Initialize database and create tables"""
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    
    # Migrate: add columns if they don't exist
    insp = inspect(engine)
    columns = [col['name'] for col in insp.get_columns('articles')]
    
    if 'is_digested' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE articles ADD COLUMN is_digested BOOLEAN DEFAULT 0"))
            conn.commit()
            print("Migrated: added 'is_digested' column to articles table")
            
    if 'click_count' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE articles ADD COLUMN click_count INTEGER DEFAULT 0"))
            conn.commit()
            print("Migrated: added 'click_count' column to articles table")
    
    print(f"Database initialized: {DATABASE_URL}")
    return engine


def get_session(engine):
    """Get a new database session"""
    Session = sessionmaker(bind=engine)
    return Session()


def check_article_exists(session, url):
    """Check if article already exists by URL"""
    article = session.query(Article).filter_by(url=url).first()
    return article is not None


if __name__ == "__main__":
    engine = init_db()
