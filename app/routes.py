from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Product, Review, Category
from app.forms import LoginForm, RegistrationForm, ProductForm, EditProfileForm, ReviewForm
from werkzeug.utils import secure_filename
import os

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    products = Product.query.order_by(Product.created_at.desc()).paginate(per_page=10)
    return render_template('home.html', products=products)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/product/<int:id>', methods=['GET', 'POST'])
def product(id):
    product = Product.query.get_or_404(id)
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(rating=form.rating.data, comment=form.comment.data, product=product, author=current_user)
        db.session.add(review)
        db.session.commit()
        flash('Your review has been posted!')
        return redirect(url_for('main.product', id=product.id))
    reviews = Review.query.filter_by(product_id=id).all()
    return render_template('product.html', product=product, form=form, reviews=reviews)

@bp.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        category = Category.query.filter_by(name=form.category.data).first()
        if category is None:
            category = Category(name=form.category.data)
            db.session.add(category)
        product = Product(title=form.title.data, description=form.description.data, price=form.price.data, category=category, author=current_user)
        db.session.add(product)
        db.session.commit()
        flash('Your product is now live!')
        return redirect(url_for('main.index'))
    return render_template('add_product.html', title='Add Product', form=form)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.profile_pic.data:
            pic_filename = secure_filename(form.profile_pic.data.filename)
            form.profile_pic.data.save(os.path.join('app/static/images/', pic_filename))
            current_user.profile_pic = pic_filename
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    products = Product.query.filter(Product.title.contains(query)).all()
    return render_template('search_results.html', products=products, query=query)