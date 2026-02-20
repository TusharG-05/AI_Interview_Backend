
from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import User, UserRole
from app.auth.security import get_password_hash

def create_admin():
    email = "admin@example.com"
    password = "admin123"
    
    try:
        with Session(engine) as session:
            user = session.exec(select(User).where(User.email == email)).first()
            if user:
                print(f"User {email} already exists. Updating password.")
                user.password_hash = get_password_hash(password)
                user.role = UserRole.ADMIN # Ensure role is admin
                session.add(user)
                session.commit()
                print("Password updated and role ensured.")
            else:
                print(f"Creating user {email}")
                user = User(
                    email=email,
                    full_name="Admin User",
                    password_hash=get_password_hash(password),
                    role=UserRole.ADMIN
                )
                session.add(user)
                session.commit()
                print("User created.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_admin()
