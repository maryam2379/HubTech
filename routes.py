from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from db import db
from models import User, Notification
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests
import json
import os

main_bp = Blueprint('main', __name__)


# ============================================
# DÉCORATEURS
# ============================================
def login_required(f):
    """Vérifie que l'utilisateur est connecté"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Récupère l'utilisateur connecté"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


# ============================================
# PAGE D'ACCUEIL
# ============================================
@main_bp.route('/')
def index():
    user = get_current_user()
    if user:
        posts = user.get_feed_posts().limit(20).all()
    else:
        from models import Post
        posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    return render_template('index.html', posts=posts, user=user)


# ============================================
# INSCRIPTION (Register)
# ============================================
# @main_bp.route('/register', methods=['GET', 'POST'])
# def register():
#     if 'user_id' in session:
#         return redirect(url_for('main.index'))
    
#     if request.method == 'POST':
#         username = request.form.get('username', '').strip().lower()
#         email = request.form.get('email', '').strip().lower()
#         password = request.form.get('password', '')
#         confirm_password = request.form.get('confirm_password', '')
#         display_name = request.form.get('display_name', '').strip()
        
#         # --- Validations ---
#         errors = []
        
#         if not username or len(username) < 3:
#             errors.append("Le nom d'utilisateur doit faire au moins 3 caractères.")
#         if not email or '@' not in email:
#             errors.append("Email invalide.")
#         if not password or len(password) < 8:
#             errors.append("Le mot de passe doit faire au moins 8 caractères.")
#         if password != confirm_password:
#             errors.append("Les mots de passe ne correspondent pas.")
        
#         # Vérifier unicité
#         if User.query.filter_by(username=username).first():
#             errors.append("Ce nom d'utilisateur est déjà pris.")
#         if User.query.filter_by(email=email).first():
#             errors.append("Cet email est déjà utilisé.")
        
#         if errors:
#             for error in errors:
#                 flash(error, 'danger')
#             return render_template('register.html')
        
#         # --- Création de l'utilisateur ---
#         new_user = User(
#             username=username,
#             email=email,
#             password_hash=generate_password_hash(password),
#             display_name=display_name or username,
#             headline=request.form.get('headline', '').strip(),
#             bio=request.form.get('bio', '').strip(),
#             location=request.form.get('location', '').strip(),
#             role=request.form.get('role', 'developer'),
#             experience_level=request.form.get('experience_level', 'junior')
#         )
        
#         db.session.add(new_user)
#         db.session.commit()
        
#         flash('Compte créé avec succès ! Connectez-vous.', 'success')
#         return redirect(url_for('main.login'))
    
#     return render_template('register.html')


# # ============================================
# # CONNEXION (Login)
# # ============================================
# @main_bp.route('/login', methods=['GET', 'POST'])
# def login():
#     if 'user_id' in session:
#         return redirect(url_for('main.index'))
    
#     if request.method == 'POST':
#         email = request.form.get('email', '').strip().lower()
#         password = request.form.get('password', '')
        
#         user = User.query.filter_by(email=email).first()
        
#         if not user:
#             flash('Email ou mot de passe incorrect.', 'danger')
#             return render_template('login.html')
        
#         if not user.is_active:
#             flash('Ce compte a été désactivé.', 'danger')
#             return render_template('login.html')
        
#         if not check_password_hash(user.password_hash, password):
#             flash('Email ou mot de passe incorrect.', 'danger')
#             return render_template('login.html')
        
#         # --- Connexion réussie ---
#         session['user_id'] = user.id
#         session['username'] = user.username
#         user.last_login = db.func.now()
#         db.session.commit()
        
#         flash(f'Bienvenue, {user.display_name or user.username} !', 'success')
        
#         next_page = request.args.get('next')
#         return redirect(next_page or url_for('main.index'))
    
#     return render_template('login.html')


# # ============================================
# # DÉCONNEXION (Logout)
# # ============================================
# @main_bp.route('/logout')
# def logout():
#     session.clear()
#     flash('Vous êtes déconnecté.', 'info')
#     return redirect(url_for('main.index'))


# # ============================================
# # PROFIL
# # ============================================
# @main_bp.route('/u/<username>')
# def profile(username):
#     user = User.query.filter_by(username=username).first_or_404()
#     current_user = get_current_user()
    
#     # Récupérer les posts du profil
#     posts = user.posts.filter_by(status='published').order_by(Post.created_at.desc()).all()
    
#     # Récupérer les projets
#     projects = user.owned_projects.order_by(Project.created_at.desc()).all()
    
#     # Vérifier si on suit cet utilisateur
#     is_following = False
#     if current_user:
#         is_following = current_user.is_following(user)
    
#     return render_template('profile.html', 
#                          profile_user=user, 
#                          posts=posts, 
#                          projects=projects,
#                          is_following=is_following,
#                          user=current_user)


# # ============================================
# # ÉDITION DU PROFIL
# # ============================================
# @main_bp.route('/profile/edit', methods=['GET', 'POST'])
# @login_required
# def edit_profile():
#     user = get_current_user()
    
#     if request.method == 'POST':
#         user.display_name = request.form.get('display_name', '').strip() or user.display_name
#         user.headline = request.form.get('headline', '').strip()
#         user.bio = request.form.get('bio', '').strip()
#         user.location = request.form.get('location', '').strip()
#         user.role = request.form.get('role', user.role)
#         user.experience_level = request.form.get('experience_level', user.experience_level)
#         user.github_url = request.form.get('github_url', '').strip()
#         user.linkedin_url = request.form.get('linkedin_url', '').strip()
#         user.portfolio_url = request.form.get('portfolio_url', '').strip()
#         user.twitter_url = request.form.get('twitter_url', '').strip()
#         user.website_url = request.form.get('website_url', '').strip()
#         user.is_available = request.form.get('is_available') == 'on'
#         user.availability_status = request.form.get('availability_status', 'not_available')
        
#         # Gestion de l'avatar (upload)
#         if 'avatar' in request.files:
#             avatar_file = request.files['avatar']
#             if avatar_file.filename:
#                 filename = f"avatar_{user.id}_{avatar_file.filename}"
#                 avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
#                 avatar_file.save(avatar_path)
#                 user.avatar = filename
        
#         db.session.commit()
#         flash('Profil mis à jour avec succès !', 'success')
#         return redirect(url_for('main.profile', username=user.username))
    
#     return render_template('edit_profile.html', user=user)


# # ============================================
# # OAUTH GOOGLE
# # ============================================
# @main_bp.route('/auth/google')
# def google_login():
#     """Redirige vers Google pour l'authentification"""
#     client_id = current_app.config.get('GOOGLE_CLIENT_ID')
#     redirect_uri = url_for('main.google_callback', _external=True)
    
#     google_auth_url = (
#         "https://accounts.google.com/o/oauth2/v2/auth"
#         f"?client_id={client_id}"
#         f"&redirect_uri={redirect_uri}"
#         "&response_type=code"
#         "&scope=openid%20email%20profile"
#         "&access_type=offline"
#     )
    
#     return redirect(google_auth_url)


# @main_bp.route('/auth/google/callback')
# def google_callback():
#     """Callback après authentification Google"""
#     code = request.args.get('code')
#     error = request.args.get('error')
    
#     if error:
#         flash('Authentification Google annulée.', 'warning')
#         return redirect(url_for('main.login'))
    
#     if not code:
#         flash('Erreur lors de la connexion avec Google.', 'danger')
#         return redirect(url_for('main.login'))
    
#     # --- Échanger le code contre un token ---
#     token_url = "https://oauth2.googleapis.com/token"
#     redirect_uri = url_for('main.google_callback', _external=True)
    
#     token_data = {
#         'code': code,
#         'client_id': current_app.config.get('GOOGLE_CLIENT_ID'),
#         'client_secret': current_app.config.get('GOOGLE_CLIENT_SECRET'),
#         'redirect_uri': redirect_uri,
#         'grant_type': 'authorization_code'
#     }
    
#     token_response = requests.post(token_url, data=token_data)
    
#     if not token_response.ok:
#         flash('Erreur lors de la connexion avec Google.', 'danger')
#         return redirect(url_for('main.login'))
    
#     tokens = token_response.json()
#     access_token = tokens.get('access_token')
    
#     # --- Récupérer les infos utilisateur ---
#     userinfo_response = requests.get(
#         'https://openidconnect.googleapis.com/v1/userinfo',
#         headers={'Authorization': f'Bearer {access_token}'}
#     )
    
#     if not userinfo_response.ok:
#         flash('Erreur lors de la récupération des informations Google.', 'danger')
#         return redirect(url_for('main.login'))
    
#     userinfo = userinfo_response.json()
    
#     google_id = userinfo.get('sub')
#     email = userinfo.get('email')
#     name = userinfo.get('name', '')
#     picture = userinfo.get('picture', '')
    
#     # --- Vérifier si l'utilisateur existe ---
#     user = User.query.filter_by(google_id=google_id).first()
    
#     if not user:
#         # Vérifier si l'email existe déjà
#         user = User.query.filter_by(email=email).first()
        
#         if user:
#             # Lier le compte Google
#             user.google_id = google_id
#             if picture and not user.avatar:
#                 user.avatar = picture
#             db.session.commit()
#         else:
#             # Créer un nouvel utilisateur
#             username = email.split('@')[0]
#             # Vérifier unicité du username
#             base_username = username
#             counter = 1
#             while User.query.filter_by(username=username).first():
#                 username = f"{base_username}{counter}"
#                 counter += 1
            
#             user = User(
#                 username=username,
#                 email=email,
#                 display_name=name,
#                 google_id=google_id,
#                 avatar=picture or 'default-avatar.png',
#                 email_verified=True
#             )
#             db.session.add(user)
#             db.session.commit()
    
#     # --- Connexion ---
#     session['user_id'] = user.id
#     session['username'] = user.username
#     user.last_login = db.func.now()
#     db.session.commit()
    
#     flash(f'Bienvenue, {user.display_name or user.username} !', 'success')
#     return redirect(url_for('main.index'))


# # ============================================
# # OAUTH GITHUB
# # ============================================
# @main_bp.route('/auth/github')
# def github_login():
#     """Redirige vers GitHub pour l'authentification"""
#     client_id = current_app.config.get('GITHUB_CLIENT_ID')
#     redirect_uri = url_for('main.github_callback', _external=True)
    
#     github_auth_url = (
#         "https://github.com/login/oauth/authorize"
#         f"?client_id={client_id}"
#         f"&redirect_uri={redirect_uri}"
#         "&scope=user:email%20read:user"
#     )
    
#     return redirect(github_auth_url)


# @main_bp.route('/auth/github/callback')
# def github_callback():
#     """Callback après authentification GitHub"""
#     code = request.args.get('code')
#     error = request.args.get('error')
    
#     if error:
#         flash('Authentification GitHub annulée.', 'warning')
#         return redirect(url_for('main.login'))
    
#     if not code:
#         flash('Erreur lors de la connexion avec GitHub.', 'danger')
#         return redirect(url_for('main.login'))
    
#     # --- Échanger le code contre un token ---
#     token_url = "https://github.com/login/oauth/access_token"
    
#     token_data = {
#         'client_id': current_app.config.get('GITHUB_CLIENT_ID'),
#         'client_secret': current_app.config.get('GITHUB_CLIENT_SECRET'),
#         'code': code,
#         'redirect_uri': url_for('main.github_callback', _external=True)
#     }
    
#     token_response = requests.post(
#         token_url,
#         data=token_data,
#         headers={'Accept': 'application/json'}
#     )
    
#     if not token_response.ok:
#         flash('Erreur lors de la connexion avec GitHub.', 'danger')
#         return redirect(url_for('main.login'))
    
#     tokens = token_response.json()
#     access_token = tokens.get('access_token')
    
#     # --- Récupérer les infos utilisateur ---
#     headers = {
#         'Authorization': f'token {access_token}',
#         'Accept': 'application/vnd.github.v3+json'
#     }
    
#     # Infos du profil
#     user_response = requests.get('https://api.github.com/user', headers=headers)
    
#     if not user_response.ok:
#         flash('Erreur lors de la récupération des informations GitHub.', 'danger')
#         return redirect(url_for('main.login'))
    
#     github_user = user_response.json()
    
#     github_id = str(github_user.get('id'))
#     username = github_user.get('login')
#     name = github_user.get('name', '') or username
#     avatar_url = github_user.get('avatar_url', '')
#     bio = github_user.get('bio', '')
#     location = github_user.get('location', '')
#     company = github_user.get('company', '')
#     blog = github_user.get('blog', '')
    
#     # Email (peut être privé, donc on fait un appel séparé)
#     email_response = requests.get('https://api.github.com/user/emails', headers=headers)
#     email = None
    
#     if email_response.ok:
#         emails = email_response.json()
#         # Prendre l'email principal et vérifié
#         for e in emails:
#             if e.get('primary') and e.get('verified'):
#                 email = e.get('email')
#                 break
#         if not email and emails:
#             email = emails[0].get('email')
    
#     if not email:
#         flash('Impossible de récupérer votre email GitHub.', 'danger')
#         return redirect(url_for('main.login'))
    
#     # --- Vérifier si l'utilisateur existe ---
#     user = User.query.filter_by(github_id=github_id).first()
    
#     if not user:
#         # Vérifier si l'email existe déjà
#         user = User.query.filter_by(email=email).first()
        
#         if user:
#             # Lier le compte GitHub
#             user.github_id = github_id
#             if avatar_url and not user.avatar:
#                 user.avatar = avatar_url
#             if bio and not user.bio:
#                 user.bio = bio
#             if not user.github_url:
#                 user.github_url = f"https://github.com/{username}"
#             db.session.commit()
#         else:
#             # Vérifier unicité du username
#             base_username = username
#             counter = 1
#             while User.query.filter_by(username=username).first():
#                 username = f"{base_username}{counter}"
#                 counter += 1
            
#             user = User(
#                 username=username,
#                 email=email,
#                 display_name=name,
#                 github_id=github_id,
#                 avatar=avatar_url or 'default-avatar.png',
#                 bio=bio,
#                 location=location,
#                 github_url=f"https://github.com/{username}",
#                 website_url=blog,
#                 headline=company,
#                 email_verified=True
#             )
#             db.session.add(user)
#             db.session.commit()
    
#     # --- Connexion ---
#     session['user_id'] = user.id
#     session['username'] = user.username
#     user.last_login = db.func.now()
#     db.session.commit()
    
#     flash(f'Bienvenue, {user.display_name or user.username} !', 'success')
#     return redirect(url_for('main.index'))


# # ============================================
# # FOLLOW / UNFOLLOW
# # ============================================
# @main_bp.route('/follow/<username>', methods=['POST'])
# @login_required
# def follow(username):
#     current_user = get_current_user()
#     user_to_follow = User.query.filter_by(username=username).first_or_404()
    
#     if current_user.id == user_to_follow.id:
#         flash("Vous ne pouvez pas vous suivre vous-même.", 'warning')
#         return redirect(url_for('main.profile', username=username))
    
#     if current_user.follow(user_to_follow):
#         # Créer une notification
#         notif = Notification(
#             user_id=user_to_follow.id,
#             notification_type='follow',
#             title='Nouveau follower',
#             message=f'{current_user.display_name or current_user.username} vous suit maintenant.',
#             actor_id=current_user.id
#         )
#         db.session.add(notif)
#         flash(f'Vous suivez maintenant {user_to_follow.display_name or username}.', 'success')
#     else:
#         flash(f'Vous suivez déjà {user_to_follow.display_name or username}.', 'info')
    
#     return redirect(url_for('main.profile', username=username))


# @main_bp.route('/unfollow/<username>', methods=['POST'])
# @login_required
# def unfollow(username):
#     current_user = get_current_user()
#     user_to_unfollow = User.query.filter_by(username=username).first_or_404()
    
#     if current_user.unfollow(user_to_unfollow):
#         flash(f'Vous ne suivez plus {user_to_unfollow.display_name or username}.', 'info')
#     else:
#         flash(f'Vous ne suiviez pas {user_to_unfollow.display_name or username}.', 'warning')
    
#     return redirect(url_for('main.profile', username=username))