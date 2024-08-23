from app import app, db, User

def create_admin_user(username, password):
    with app.app_context():
        db.create_all()
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"Admin user '{username}' created successfully.")
        else:
            print(f"User '{username}' already exists.")

if __name__ == "__main__":
    create_admin_user("admin", "your_secure_password")
    