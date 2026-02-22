# create_admin.py
from app.core.database import SessionLocal
from app.models.organization import User
from app.models.workflow import FormSubmission
from app.core.security import get_password_hash

def create_superuser():
    db = SessionLocal()
    email = "admin@gmail.com"
    password = "think@123"
    
    # Check if admin already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print("Admin user already exists!")
        db.close()
        return

    # Create the admin user
    admin_user = User(
        email=email,
        full_name="System Administrator",
        hashed_password=get_password_hash(password),
        is_active=True,
        is_admin=True  # This is the magic flag!
    )
    
    db.add(admin_user)
    db.commit()
    print(f"Super Admin created successfully!")
    print(f"Email: {email}")
    print(f"Password: {password}")
    
    db.close()

if __name__ == "__main__":
    create_superuser()