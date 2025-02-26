from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.sql import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///photogram.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Check that upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)

db = SQLAlchemy(app)

# Create User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_image = db.Column(db.String(100), default='default.jpg')
    bio = db.Column(db.String(250), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('Like', backref='user', lazy=True, cascade="all, delete-orphan")
    
    # Followers relationship (self-referential)
    followed = db.relationship(
        'Follow',
        foreign_keys='Follow.follower_id',
        backref=db.backref('follower', lazy='joined'),
        lazy='dynamic',
        cascade="all, delete-orphan"
    )
    
    followers = db.relationship(
        'Follow',
        foreign_keys='Follow.followed_id',
        backref=db.backref('followed', lazy='joined'),
        lazy='dynamic',
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_following(self, user):
        return Follow.query.filter_by(
            follower_id=self.id,
            followed_id=user.id
        ).count() > 0
    
    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower_id=self.id, followed_id=user.id)
            db.session.add(follow)
    
    def unfollow(self, user):
        follow = Follow.query.filter_by(
            follower_id=self.id,
            followed_id=user.id
        ).first()
        if follow:
            db.session.delete(follow)

# Create Follow Model (for user following relationship)
class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create Like Model
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add unique constraint to prevent multiple likes from same user
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)

# Create Comment Model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def time_since(self):
        """Returns a human-readable time string like '2 hours ago'"""
        delta = datetime.utcnow() - self.created_at
        
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"

# Create Post Model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('Like', backref='post', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Post {self.id}>'
    
    def time_since(self):
        """Returns a human-readable time string like '2 hours ago'"""
        delta = datetime.utcnow() - self.created_at
        
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"
    
    def is_liked_by(self, user):
        return Like.query.filter_by(user_id=user.id, post_id=self.id).count() > 0

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Check for allowed image file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Create the database
with app.app_context():
    db.create_all()

# Auth routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Create a route for login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Login failed. Please check your username and password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Create a route for viewing a profile 
@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    
    is_following = False
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
        if current_user:
            is_following = current_user.is_following(user)
    
    follower_count = Follow.query.filter_by(followed_id=user.id).count()
    following_count = Follow.query.filter_by(follower_id=user.id).count()
    
    return render_template('profile.html', 
                          user=user, 
                          posts=posts, 
                          is_following=is_following,
                          follower_count=follower_count, 
                          following_count=following_count)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user_to_follow = User.query.filter_by(username=username).first_or_404()
    current_user = User.query.get(session['user_id'])
    
    if current_user.id == user_to_follow.id:
        flash('You cannot follow yourself', 'danger')
    else:
        current_user.follow(user_to_follow)
        db.session.commit()
        flash(f'You are now following {username}', 'success')
    
    return redirect(url_for('profile', username=username))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user_to_unfollow = User.query.filter_by(username=username).first_or_404()
    current_user = User.query.get(session['user_id'])
    
    current_user.unfollow(user_to_unfollow)
    db.session.commit()
    flash(f'You have unfollowed {username}', 'info')
    
    return redirect(url_for('profile', username=username))

# Updated routes
@app.route('/')
def index():
    if 'user_id' in session:
        # Show posts from followed users for logged-in users
        current_user = User.query.get(session['user_id'])
        followed_users = [follow.followed_id for follow in current_user.followed.all()]
        followed_users.append(current_user.id)  # Include user's own posts
        
        posts = Post.query.filter(Post.user_id.in_(followed_users)).order_by(Post.created_at.desc()).all()
    else:
        # Show all posts for non-logged in users
        posts = Post.query.order_by(Post.created_at.desc()).all()
    
    return render_template('index.html', posts=posts)

@app.route('/explore')
def explore():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('explore.html', posts=posts)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', post=post)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        # Check if image file exists in the request
        if 'image' not in request.files:
            flash('No image file selected', 'danger')
            return redirect(request.url)
            
        file = request.files['image']
        
        # Check if user submitted an empty form (browser submits empty file without filename)
        if file.filename == '':
            flash('No image file selected', 'danger')
            return redirect(request.url)
            
        # Process file if it exists and has allowed extension
        if file and allowed_file(file.filename):
            # Create unique filename to avoid collisions
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            
            # Save the file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Get caption from form
            caption = request.form.get('caption', '')
            
            # Create new post
            new_post = Post(
                image_filename=unique_filename,
                caption=caption,
                user_id=session['user_id']
            )
            
            db.session.add(new_post)
            db.session.commit()
            
            flash('Your post has been created!', 'success')
            return redirect(url_for('post_detail', post_id=new_post.id))
        else:
            flash('Invalid file type. Allowed types: png, jpg, jpeg, gif', 'danger')
            return redirect(request.url)
            
    return render_template('create.html')

@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    current_user = User.query.get(session['user_id'])
    
    # Check if user already liked the post
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        db.session.commit()
    else:
        # Like
        new_like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)
        db.session.commit()
    
    # Redirect back to referring page (either index or post_detail)
    next_page = request.referrer
    if not next_page:
        next_page = url_for('index')
    return redirect(next_page)

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    comment_content = request.form.get('content', '')
    
    if comment_content.strip():
        comment = Comment(
            content=comment_content,
            post_id=post.id,
            user_id=session['user_id']
        )
        db.session.add(comment)
        db.session.commit()
    
    # Redirect back to post detail
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # Update bio
        bio = request.form.get('bio', '')
        user.bio = bio
        
        # Handle profile image update
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            
            if file.filename != '':
                if file and allowed_file(file.filename):
                    # Create unique filename
                    filename = secure_filename(file.filename)
                    file_ext = os.path.splitext(filename)[1]
                    unique_filename = f"profile_{uuid.uuid4().hex}{file_ext}"
                    
                    # Save the file
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', unique_filename)
                    file.save(file_path)
                    
                    # Update user profile image
                    user.profile_image = f'profiles/{unique_filename}'
                else:
                    flash('Invalid file type. Allowed types: png, jpg, jpeg, gif', 'danger')
                    return redirect(url_for('edit_profile'))
        
        db.session.commit()
        flash('Your profile has been updated', 'success')
        return redirect(url_for('profile', username=user.username))
    
    return render_template('edit_profile.html', user=user)

@app.template_filter('file_url')
def file_url(filename):
    """Template filter to generate URL for uploaded files"""
    return url_for('static', filename=f'uploads/{filename}')

@app.template_filter('like_count')
def like_count(post):
    """Template filter to count likes for a post"""
    return Like.query.filter_by(post_id=post.id).count()

@app.context_processor
def utility_processor():
    def is_liked_by_user(post, user_id):
        """Check if a post is liked by the current user"""
        return Like.query.filter_by(post_id=post.id, user_id=user_id).count() > 0
    
    def get_user(user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    return dict(is_liked_by_user=is_liked_by_user, get_user=get_user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
