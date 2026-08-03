#======Password Validator======

def passwordValidator(password: str):
	if len(password) < 8:
		return "Your password needs at least 8 characters."

	has_digit = any(ch.isdigit() for ch in password)
	has_upper = any(ch.isupper() for ch in password)
	has_lower = any(ch.islower() for ch in password)
	has_symbol = any(not ch.isalnum() for ch in password)

	if not has_digit:
		return "Your password should contain at least one number."
	if not has_upper:
		return "Your password should contain at least one uppercase letter."
	if not has_lower:
		return "Your password should contain at least one lowercase letter."
	if not has_symbol:
		return "Your password should contain at least one symbol (e.g. !@#$%)."

	return "Strong Password"
