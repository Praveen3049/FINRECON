from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.core.security import hash_password
from app.models.user import User, UserRole

# Standard Development Seed Users for Hackathon & Role-Based Testing
DEMO_USERS: List[Dict[str, Any]] = [
    {
        "name": "Alex Rivera",
        "email": "user@finrecon.com",
        "password": "User@123",
        "role": UserRole.USER,
    },
    {
        "name": "Elena Rostova",
        "email": "auditor@finrecon.com",
        "password": "Auditor@123",
        "role": UserRole.AUDITOR,
    },
    {
        "name": "Marcus Vance",
        "email": "manager@finrecon.com",
        "password": "Manager@123",
        "role": UserRole.MANAGER,
    },
    {
        "name": "FinRecon Administrator",
        "email": "admin@finrecon.com",
        "password": "Admin@123",
        "role": UserRole.MANAGER,
    },
    {
        "name": "Operations Lead",
        "email": "manager@test.com",
        "password": "Manager@123",
        "role": UserRole.MANAGER,
    },
    {
        "name": "Lead Auditor",
        "email": "auditor@test.com",
        "password": "Auditor@123",
        "role": UserRole.AUDITOR,
    },
]


def seed_demo_users(db: Session) -> int:
    """
    Ensure demonstration users exist in the database for USER, AUDITOR, and MANAGER roles.
    Idempotent: skips any users that already exist.
    """
    seeded_count = 0
    for demo in DEMO_USERS:
        existing = db.query(User).filter(User.email == demo["email"]).first()
        if not existing:
            user = User(
                name=demo["name"],
                email=demo["email"],
                password_hash=hash_password(demo["password"]),
                role=demo["role"],
                is_active=True,
            )
            db.add(user)
            seeded_count += 1
            logger.info(f"Seeded demo user: {demo['email']} [{demo['role'].value}]")

    if seeded_count > 0:
        db.commit()
    return seeded_count
