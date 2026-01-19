from passlib.context import CryptContext

# bcrypt 사용 권장
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str, show_pw: bool = False) -> str:
    hashed_pw = pwd_context.hash(password)
    if show_pw:
        print(f"password: {password}")
        print(f"hashed_pw: {hashed_pw}")
    return hashed_pw
