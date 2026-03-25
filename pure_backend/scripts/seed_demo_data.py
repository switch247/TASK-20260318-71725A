import json

from src.db.base import Base
from src.db.session import SessionLocal, engine
from src.services.demo_seed_service import seed_demo_dataset


def main() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        result = seed_demo_dataset(session)
        print(json.dumps(result, indent=2))
    finally:
        session.close()


if __name__ == "__main__":
    main()
