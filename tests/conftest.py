"""Pytest Configuration und Fixtures."""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from packages.common.db_models import Base


@pytest.fixture(scope="session")
def test_database_url():
    """Test-Database URL."""
    return os.environ.get(
        "TEST_DATABASE_URL",
        "sqlite+pysqlite:///:memory:"
    )


@pytest.fixture(scope="session")
def engine(test_database_url):
    """SQLAlchemy Engine für Tests."""
    engine = create_engine(test_database_url, echo=False)
    
    # Erstelle alle Tabellen
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup: Lösche alle Tabellen
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine):
    """Database Session für Tests."""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()

