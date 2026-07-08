from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import db
from models import User, Post, Follow

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Logique d'inscription
        pass
    return render_template('register.html')

@main_bp.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)