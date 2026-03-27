import json

from src.db.base import Base
import src.db.session as db_session
from src.db.session import engine
from src.services.demo_seed_service import seed_demo_dataset


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db_session.ensure_engine()
    session = db_session.SessionLocal()
    try:
        result = seed_demo_dataset(session)
        print(json.dumps(result, indent=2))
    finally:
        session.close()


if __name__ == "__main__":
    main()
