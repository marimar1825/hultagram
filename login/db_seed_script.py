from app import app, db, User, Post, Comment, Like, Follow
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import os
import shutil
import uuid

# Sample data
users = [
    {'username': 'prof_todd', 'email': 'prof_todd@hult.edu', 'password': 'password456', 'bio': 'Computer Science Professor'},
    {'username': 'natalie', 'email': 'natalie@hult.edu', 'password': 'password123', 'bio': 'Photography enthusiast'},
    {'username': 'asmi', 'email': 'asmi@hult.edu', 'password': 'password123', 'bio': 'Travel blogger'},
    {'username': 'aaron', 'email': 'aaron@hult.edu', 'password': 'password123', 'bio': 'Food lover'},
    {'username': 'mariana', 'email': 'mariana@hult.edu', 'password': 'password123', 'bio': 'Fitness coach'},
    {'username': 'artur', 'email': 'artur@hult.edu', 'password': 'password123', 'bio': 'Loves Macarena'},
    {'username': 'alan', 'email': 'alan@hult.edu', 'password': 'password123', 'bio': 'Slava Ukraine!'}
]

# Sample post captions
captions = [
    "Beautiful day at the beach! 🏖️",
    "Exploring the city today 🏙️",
    "Just finished this amazing book 📚",
    "Coffee vibes ☕",
    "Sunset views 🌅",
    "Weekend hike with friends 🥾",
    "Trying out a new recipe 🍳",
    "My workspace setup 💻",
    "Art gallery visit 🎨",
    "Family time ❤️"
]

# Sample comments
comments = [
    "Love this!",
    "Amazing photo!",
    "Where is this?",
    "Looking good!",
    "Great shot!",
    "I need to visit this place",
    "Beautiful!",
    "This is awesome",
    "Thanks for sharing",
    "So creative!"
]

def seed_database():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        print("Creating users...")
        created_users = []
        for user_data in users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                bio=user_data['bio']
            )
            db.session.add(user)
            created_users.append(user)
        
        db.session.commit()
        
        # Create sample posts
        print("Creating posts...")
        
        # Ensure uploads directory exists
        uploads_dir = os.path.join('static', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Copy sample images or create placeholders
        # In a real implementation, you would have sample images to copy
        # For this example, we'll create text files as placeholders
        created_posts = []
        for i in range(15):  # Create 15 posts
            user = random.choice(created_users)
            
            # For a real implementation, copy an image file
            # Here we're creating a placeholder unique filename
            unique_filename = f"{uuid.uuid4().hex}.jpg"
            
            # In a real implementation, you would copy a real image:
            # shutil.copy('sample_images/image1.jpg', os.path.join(uploads_dir, unique_filename))
            
            # Create a placeholder file for demonstration
            with open(os.path.join(uploads_dir, unique_filename), 'w') as f:
                f.write(f"Placeholder for post {i+1}")
            
            # Create a random timestamp within the last 30 days
            random_days = random.randint(0, 30)
            created_at = datetime.utcnow() - timedelta(days=random_days)
            
            post = Post(
                image_filename=unique_filename,
                caption=random.choice(captions),
                created_at=created_at,
                user_id=user.id
            )
            db.session.add(post)
            created_posts.append(post)
        
        db.session.commit()
        
        # Create comments
        print("Creating comments...")
        for post in created_posts:
            # Add 1-5 comments per post
            for _ in range(random.randint(1, 5)):
                user = random.choice(created_users)
                
                # Random timestamp after post but before now
                post_time = post.created_at
                now = datetime.utcnow()
                comment_time = post_time + timedelta(
                    seconds=random.randint(1, int((now - post_time).total_seconds()))
                )
                
                comment = Comment(
                    content=random.choice(comments),
                    created_at=comment_time,
                    post_id=post.id,
                    user_id=user.id
                )
                db.session.add(comment)
        
        db.session.commit()
        
        # Create likes
        print("Creating likes...")
        for post in created_posts:
            # Randomly assign 0-5 likes per post
            liking_users = random.sample(created_users, random.randint(0, min(5, len(created_users))))
            for user in liking_users:
                like = Like(
                    user_id=user.id,
                    post_id=post.id
                )
                db.session.add(like)
        
        db.session.commit()
        
        # Create follows
        print("Creating follows...")
        for user in created_users:
            # Each user follows 1-3 random users
            users_to_follow = random.sample(
                [u for u in created_users if u != user],
                random.randint(1, min(3, len(created_users) - 1))
            )
            
            for followed_user in users_to_follow:
                follow = Follow(
                    follower_id=user.id,
                    followed_id=followed_user.id
                )
                db.session.add(follow)
        
        db.session.commit()
        
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()