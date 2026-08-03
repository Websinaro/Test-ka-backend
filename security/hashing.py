from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"],deprecated="auto")

def hashPass(password : str) -> str:
	return pwd_context.hash(password)
	
def verifyPass(plain_pass: str, hash_pass: str) -> bool:
	return pwd_context.verify(plain_pass,hash_pass)
