import re
from django.core.exceptions import ValidationError


class SimplePasswordValidator:
    """
    Requires:
    - At least 8 characters
    - At least one uppercase letter
    - At least one special character
    """
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[^a-zA-Z0-9]', password):
            raise ValidationError("Password must contain at least one special character.")

    def get_help_text(self):
        return "Must be at least 8 characters long, contain at least one uppercase letter and one special character."
