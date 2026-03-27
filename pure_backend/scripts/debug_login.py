import os
from datetime import UTC, datetime, timedelta

os.environ.setdefault("ENFORCE_HTTPS", "false")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("TEST_DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "sqlite+pysqlite://"))
TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from src.db.base import Base
import src.models  # register models
from src.services.crypto_service import encrypt_sensitive, hash_password
from src.services.seed_service import seed_role_permissions
from src.models.identity import Organization, OrganizationMembership, User
from src.models.enums import RoleName, MembershipStatus
from src.api.v1.dependencies import get_session

def main():
    connect_args = {"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
    engine_kwargs = {}
    if connect_args:
        engine_kwargs["connect_args"] = connect_args
        engine_kwargs["poolclass"] = StaticPool

    engine = create_engine(TEST_DATABASE_URL, **engine_kwargs)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # bind app session
    import src.db.session as app_db_session
    app_db_session.engine = engine
    app_db_session.SessionLocal = SessionLocal

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_role_permissions(db)
        org = Organization(code="TESTORG", name="Test Org", is_active=True)
        db.add(org)
        db.flush()

        reviewer = User(
            username="reviewer_test",
            password_hash=hash_password("Reviewer1234"),
            display_name="Reviewer User",
            status="active",
            email_encrypted=encrypt_sensitive("reviewer_test@example.com"),
        )
        db.add(reviewer)
        db.flush()
        db.add(
            OrganizationMembership(
                organization_id=org.id,
                user_id=reviewer.id,
                role_name=RoleName.REVIEWER,
                status=MembershipStatus.ACTIVE,
            )
        )
        db.commit()
        # quick sanity-check: ensure passlib can verify the stored hash
        from src.services.crypto_service import verify_password
        print('verify_password(stored):', verify_password('Reviewer1234', reviewer.password_hash))
    finally:
        db.close()

    from src.main import app
    app.dependency_overrides[get_session] = lambda: SessionLocal()
    client = TestClient(app)
    resp = client.post("/api/v1/auth/login", json={"username": "reviewer_test", "password": "Review1234"})
    print("status:", resp.status_code)
    try:
        print(resp.json())
    except Exception:
        print(resp.text)

if __name__ == '__main__':
    main()
