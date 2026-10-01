from app.core.database import engine, Base
from app.core.logging import logger
import app.models  # Ensures all 10 models are imported


def init_db():
    logger.info("Initializing database tables and indexes...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables successfully created: " + ", ".join(Base.metadata.tables.keys()))


if __name__ == "__main__":
    init_db()
