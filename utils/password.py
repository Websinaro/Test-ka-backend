#======Password Validator======
'''MUBARAK VERSION'''

def passwordValidator(password):
	has_digit=False
	has_upper=False
	has_lower=False
	has_symbol=False
	
	if len(password)<8:
		print("Your Password need atleast 8 characters..")
		return False

	for ch in password:
		if ch.isdigit():
			has_digit=True
		elif ch.isupper():
			has_upper=True
		elif ch.islower():
			has_lower=True
		elif not ch.isalnum():
			has_symbol=True
			
	if not has_digit:
		return "Your Password should contain Numbers!!"
	if not has_upper:
		return "Your password should contain Uppercase character "
	if not has_lower:
		return "Your password should contain Lowercase character "
	if not has_symbol:
		return "Your Password should contain symbols "
		
	if has_digit and has_upper and has_lower and has_symbol:
		return "Strong Password"
