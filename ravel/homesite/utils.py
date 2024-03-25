import re

# check the validity of an email with regex
def is_valid_email(email) -> bool:
    email_re = r"[a-zA-Z0-9._%+-~]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}"
    if len(re.findall(email_re, email)) == 1:
        return True
    else:
        return False