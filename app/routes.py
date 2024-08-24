
from flask import Blueprint, abort, render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_user, logout_user, login_required

from werkzeug.utils import secure_filename
import os
from app import db
from app.models import Cart, CartItem, Product, Wishlist, User, Review, Category, ProductImage, Order, Message
from app.forms import LoginForm, MessageForm, RegistrationForm, ProductForm, EditProfileForm, ReviewForm, SearchForm
from app.Decorator import admin_required
from config import allowed_file

# Blueprint setup
bp = Blueprint('main', __name__)

# Function to save profile picture
def save_profile_picture(form_picture):
    picture_fn = secure_filename(form_picture.filename)
    picture_path = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], picture_fn)
    form_picture.save(picture_path)
    return picture_fn


# Routes
@bp.route('/')
@bp.route('/index')
@login_required
def index():
    products = Product.query.order_by(Product.created_at.desc()).paginate(per_page=10)
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart_item_count = len(CartItem.query.filter_by(cart_id=cart.id).all()) if cart else 0
    
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
        # Calculate unread messages count
    unread_count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()
    
    
    return render_template('home.html', products=products, cart_item_count=cart_item_count, wishlist_items=wishlist_items, unread_count=unread_count)

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        # Calculate unread messages count
        unread_count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()
        # Make it available to all templates
        current_app.jinja_env.globals['unread_count'] = unread_count
        
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
        
        print(f"Registering user: {user.username}, {user.email}")
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            flash('An error occurred. Please try again.')
    
    return render_template('register.html', title='Register', form=form)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.profile_pic.data:
            pic_filename = save_profile_picture(form.profile_pic.data)
            current_user.profile_pic = pic_filename
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('edit_profile.html', title='Edit Profile', form=form)

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
    
    is_uploader = product.author == current_user
    reviews = Review.query.filter_by(product_id=id).all()
    return render_template('product.html', product=product, form=form, reviews=reviews, is_uploader=is_uploader)


@bp.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        category = Category.query.filter_by(name=form.category.data).first()
        if category is None:
            category = Category(name=form.category.data)
            db.session.add(category)

        product = Product(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            category=category,
            author=current_user,
        )
        db.session.add(product)
        db.session.flush()  # Ensure the product ID is available before saving images

        for image in form.images.data:
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join('app/static/images/', filename))
                product_image = ProductImage(product_id=product.id, image_filename=filename)
                db.session.add(product_image)

        db.session.commit()
        flash('Your product is now live!')
        return redirect(url_for('main.index'))
    return render_template('add_product.html', title='Add Product', form=form)



@bp.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    query = form.query.data
    min_price = form.min_price.data
    max_price = form.max_price.data

    products_query = Product.query

    if query:
        products_query = products_query.filter(Product.title.ilike(f'%{query}%'))

    if min_price is not None:
        products_query = products_query.filter(Product.price >= min_price)
        
    if max_price is not None:
        products_query = products_query.filter(Product.price <= max_price)

    products = products_query.all()
    return render_template('search.html', products=products, form=form)

@bp.route('/buy_product/<int:id>', methods=['POST'])
@login_required
def buy_product(id):
    product = Product.query.get_or_404(id)
    if product.author == current_user or product.is_sold:
        flash('You cannot buy this product.')
        return redirect(url_for('main.index'))
    
    product.is_sold = True
    db.session.commit()
    flash('You have successfully bought the product!')
    return redirect(url_for('main.product', id=product.id))

@bp.route('/sell_product/<int:id>', methods=['POST'])
@login_required
def sell_product(id):
    product = Product.query.get_or_404(id)
    if product.author != current_user or product.is_sold:
        flash('You cannot sell this product.')
        return redirect(url_for('main.index'))
    
    product.is_sold = True
    db.session.commit()
    flash('Your product has been sold!')
    return redirect(url_for('main.index'))

@bp.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('orders.html', orders=orders)

@bp.route('/send_message', methods=['GET', 'POST'])
@login_required
def send_message():
    form = MessageForm()
    if form.validate_on_submit():
        recipient = User.query.filter_by(username=form.recipient.data).first()
        if recipient is None:
            flash('User not found.')
            return redirect(url_for('main.send_message'))

        message = Message(
            sender_id=current_user.id,
            receiver_id=recipient.id,
            body=form.body.data
        )
        db.session.add(message)
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('main.index'))
    return render_template('send_message.html', title='Send Message', form=form)

@bp.route('/inbox')
@login_required
def inbox():
    # Query messages directly from the Message model
    messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    return render_template('inbox.html', title='Inbox', messages=messages)

@bp.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    
    if product.user_id == current_user.id:
        flash('You cannot add your own product to your wishlist.', 'danger')
        return redirect(url_for('main.product', id=product_id))
    
    existing_wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if existing_wishlist_item:
        flash('Product is already in your wishlist.', 'info')
    else:
        new_wishlist_item = Wishlist(user_id=current_user.id, product_id=product.id)
        db.session.add(new_wishlist_item)
        db.session.commit()
        flash('Product added to wishlist!', 'success')
    
    return redirect(url_for('main.product', id=product_id))

@bp.route('/wishlist')
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', wishlist_items=wishlist_items)

@bp.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin_dashboard.html', title='Admin Dashboard', users=users, products=products, categories=categories)

@bp.route('/remove_from_wishlist/<int:wishlist_id>', methods=['POST'])
@login_required
def remove_from_wishlist(wishlist_id):
    wishlist_item = Wishlist.query.get_or_404(wishlist_id)
    
    if wishlist_item.user_id != current_user.id:
        abort(403)
    
    db.session.delete(wishlist_item)
    db.session.commit()
    flash('Product removed from wishlist!', 'success')
    return redirect(url_for('main.wishlist'))

@bp.route('/purchase_product/<int:product_id>', methods=['POST'])
@login_required
def purchase_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product in [item.product for item in current_user.wishlist]:
        wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first()
        db.session.delete(wishlist_item)
        db.session.commit()
    product.owner_id = current_user.id
    db.session.commit()
    flash('Product purchased successfully!', 'success')
    return redirect(url_for('dashboard'))

@bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product.id)
        db.session.add(cart_item)

    db.session.commit()
    flash('Product added to cart!', 'success')
    return redirect(url_for('main.index'))

@bp.route('/cart')
@login_required
def cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if cart:
        items = CartItem.query.filter_by(cart_id=cart.id).all()
    else:
        items = []

    print(f"Cart Items: {items}") 
    return render_template('cart.html', cart=cart, items=items)

@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        flash('Your cart is empty.', 'danger')
        return redirect(url_for('main.cart'))

    for item in cart.items:
        product = Product.query.get_or_404(item.product_id)
        if not product.is_sold:
            product.is_sold = True
            order = Order(product_id=product.id, user_id=current_user.id)
            db.session.add(order)
    
    db.session.delete(cart)
    db.session.commit()
    flash('Checkout successful!', 'success')
    return redirect(url_for('main.index'))

@bp.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.cart.user_id != current_user.id:
        abort(403)
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Product removed from cart!', 'success')
    return redirect(url_for('main.cart'))

@bp.route('/user_profile')
@login_required
def user_profile():
    stats = current_user.product_stats
    return render_template('user_profile.html', stats=stats)

@bp.route('/remove_product/<int:id>', methods=['POST'])
@login_required
@admin_required
def remove_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product has been removed!', 'success')
    return redirect(url_for('main.index'))