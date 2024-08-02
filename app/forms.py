from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FloatField, FileField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Optional
from wtforms.fields.simple import FileField
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ProductForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    image = FileField('Product Image')
    submit = SubmitField('Add Product')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_pic = FileField('Update Profile Picture')
    submit = SubmitField('Save Changes')

class ReviewForm(FlaskForm):
    rating = StringField('Rating', validators=[DataRequired()])
    comment = TextAreaField('Comment')
    submit = SubmitField('Submit Review')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    min_price = FloatField('Min Price', validators=[Optional()])
    max_price = FloatField('Max Price', validators=[Optional()])
    submit = SubmitField('Search')