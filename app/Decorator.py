from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You need to log in first.')
            return redirect(url_for('auth.login'))
        if not current_user.admin_profile:  # Assuming an admin profile exists
            flash('You do not have permission to access this page.')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function