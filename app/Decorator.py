from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from app.models import Admin

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You need to log in first.')
            return redirect(url_for('main.login'))
        
        # Check if the user is an admin or superadmin
        admin_profile = Admin.query.filter_by(user_id=current_user.id).first()
        if not admin_profile or not (admin_profile.is_superadmin or current_user.admin_profile):
            flash('You do not have permission to access this page.')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function