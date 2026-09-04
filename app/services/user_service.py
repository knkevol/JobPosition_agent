from sqlalchemy.orm import Session

from app.models.user import User

DEFAULT_USER_EMAIL = "me@local"

# 이메일과 일치하는 사용자가 있으면 반환, 없으면 만든다
def get_or_create_default_user(db: Session) -> User:
    user = db.query(User).filter(User.email == DEFAULT_USER_EMAIL).first()
    if user is None:
        user = User(name="Me", email=DEFAULT_USER_EMAIL)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

