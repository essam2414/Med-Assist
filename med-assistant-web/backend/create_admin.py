# backend/create_admin.py
from app.db import SessionLocal
from app.models.user import User
from app.auth import hash_password

def create_admin(name: str, email: str, password: str):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User with email {email} already exists (role={existing.role})")
            return

        user = User(
            name=name,
            email=email,
            role="admin",
            hashed_password=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created admin user: id={user.id}, email={user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    # CHANGE THESE VALUES to what you want
    create_admin(
        name="Essam Sheikh",
        email="essamsheikh24@gmail.com",
        password="password",
    )
