from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, abort
from db import db
from models import User, Post, Project, Comment, Tag, Notification, Message, Job, JobApplication, CodeSnippet
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
import os
import requests

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
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Récupère l'utilisateur connecté"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


# ============================================
# PAGE D'ACCUEIL & FEED
# ============================================
@main_bp.route('/')
def index():
    """Page d'accueil avec le feed"""
    user = get_current_user()
    if user:
        posts = user.get_feed_posts().limit(20).all()
    else:
        posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    return render_template('index.html', posts=posts, user=user)


# ============================================
# INSCRIPTION (Register)
# ============================================
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription multi-étapes"""
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        display_name = request.form.get('display_name', '').strip()

        # --- Validations ---
        errors = []

        if not username or len(username) < 3:
            errors.append("Le nom d'utilisateur doit faire au moins 3 caractères.")
        if not email or '@' not in email:
            errors.append("Email invalide.")
        if not password or len(password) < 8:
            errors.append("Le mot de passe doit faire au moins 8 caractères.")
        if password != confirm_password:
            errors.append("Les mots de passe ne correspondent pas.")

        # Vérifier unicité
        if User.query.filter_by(username=username).first():
            errors.append("Ce nom d'utilisateur est déjà pris.")
        if User.query.filter_by(email=email).first():
            errors.append("Cet email est déjà utilisé.")

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')

               # --- Création de l'utilisateur ---
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            display_name=display_name or username,
            headline=request.form.get('headline', '').strip(),
            bio=request.form.get('bio', '').strip(),
            location=request.form.get('location', '').strip(),
            role=request.form.get('role', 'developer'),
            experience_level=request.form.get('experience_level', 'junior')
        )

        db.session.add(new_user)
        db.session.flush()  # Génère l'ID de l'utilisateur pour les relations

        # Gestion des intérêts (tags)
        interests_raw = request.form.get('interests', '')
        if interests_raw:
            interest_names = [i.strip() for i in interests_raw.split(',') if i.strip()]
            for interest_name in interest_names:
                tag = Tag.query.filter_by(slug=interest_name.lower()).first()
                if not tag:
                    tag = Tag(name=interest_name.capitalize(), slug=interest_name.lower())
                    db.session.add(tag)
                    db.session.flush()  # Génère l'ID du tag
                new_user.skills.append(tag)

        try:
            db.session.commit()
            flash('Compte créé avec succès ! Connectez-vous.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du compte : {str(e)}', 'danger')
            return render_template('auth/register.html')

        flash('Compte créé avec succès ! Connectez-vous.', 'success')
        return redirect(url_for('main.login'))

    return render_template('auth/register.html')


# ============================================
# CONNEXION (Login)
# ============================================
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Email ou mot de passe incorrect.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Ce compte a été désactivé.', 'danger')
            return render_template('auth/login.html')

        if not check_password_hash(user.password_hash, password):
            flash('Email ou mot de passe incorrect.', 'danger')
            return render_template('auth/login.html')

        # --- Connexion réussie ---
        session['user_id'] = user.id
        session['username'] = user.username
        user.last_login = db.func.now()
        db.session.commit()

        flash(f'Bienvenue, {user.display_name or user.username} !', 'success')

        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    return render_template('auth/login.html')


# ============================================
# DÉCONNEXION (Logout)
# ============================================
@main_bp.route('/logout')
def logout():
    """Déconnexion de l'utilisateur"""
    session.clear()
    flash('Vous êtes déconnecté.', 'info')
    return redirect(url_for('main.index'))


# ============================================
# OAUTH - GOOGLE
# ============================================
@main_bp.route('/auth/google')
def google_login():
    """Redirige vers Google pour l'authentification"""
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    if not client_id:
        flash("La connexion Google n'est pas configurée.", 'warning')
        return redirect(url_for('main.login'))

    # FORCER localhost pour matcher la config Google Cloud Console
    redirect_uri = "http://localhost:5000/auth/google/callback"

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
    )

    return redirect(google_auth_url)


@main_bp.route('/auth/google/callback')
def google_callback():
    """Callback après authentification Google"""
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        flash('Authentification Google annulée.', 'warning')
        return redirect(url_for('main.login'))

    if not code:
        flash('Erreur lors de la connexion avec Google.', 'danger')
        return redirect(url_for('main.login'))

    # --- Échanger le code contre un token ---
    token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = "http://localhost:5000/auth/google/callback"

    token_data = {
        'code': code,
        'client_id': current_app.config.get('GOOGLE_CLIENT_ID'),
        'client_secret': current_app.config.get('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    token_response = requests.post(token_url, data=token_data)

    if not token_response.ok:
        flash('Erreur lors de la connexion avec Google.', 'danger')
        return redirect(url_for('main.login'))

    tokens = token_response.json()
    access_token = tokens.get('access_token')

    # --- Récupérer les infos utilisateur ---
    userinfo_response = requests.get(
        'https://openidconnect.googleapis.com/v1/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    if not userinfo_response.ok:
        flash('Erreur lors de la récupération des informations Google.', 'danger')
        return redirect(url_for('main.login'))

    userinfo = userinfo_response.json()

    google_id = userinfo.get('sub')
    email = userinfo.get('email')
    name = userinfo.get('name', '')
    picture = userinfo.get('picture', '')

    # --- Vérifier si l'utilisateur existe ---
    user = User.query.filter_by(google_id=google_id).first()

    if not user:
        # Vérifier si l'email existe déjà
        user = User.query.filter_by(email=email).first()

        if user:
            # Lier le compte Google
            user.google_id = google_id
            if picture and not user.avatar:
                user.avatar = picture
            db.session.commit()
        else:
            # Créer un nouvel utilisateur
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                display_name=name,
                google_id=google_id,
                avatar=picture or 'default-avatar.png',
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()

    # --- Connexion ---
    session['user_id'] = user.id
    session['username'] = user.username
    user.last_login = db.func.now()
    db.session.commit()

    flash(f'Bienvenue, {user.display_name or user.username} !', 'success')
    return redirect(url_for('main.index'))


# ============================================
# OAUTH - GITHUB
# ============================================
@main_bp.route('/auth/github')
def github_login():
    """Redirige vers GitHub pour l'authentification"""
    client_id = current_app.config.get('GITHUB_CLIENT_ID')
    if not client_id:
        flash("La connexion GitHub n'est pas configurée.", 'warning')
        return redirect(url_for('main.login'))

    # FORCER localhost pour matcher la config GitHub OAuth App
    redirect_uri = "http://localhost:5000/auth/github/callback"

    github_auth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&scope=user:email%20read:user"
    )

    return redirect(github_auth_url)


@main_bp.route('/auth/github/callback')
def github_callback():
    """Callback après authentification GitHub"""
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        flash('Authentification GitHub annulée.', 'warning')
        return redirect(url_for('main.login'))

    if not code:
        flash('Erreur lors de la connexion avec GitHub.', 'danger')
        return redirect(url_for('main.login'))

    # --- Échanger le code contre un token ---
    token_url = "https://github.com/login/oauth/access_token"
    redirect_uri = "http://localhost:5000/auth/github/callback"

    token_data = {
        'client_id': current_app.config.get('GITHUB_CLIENT_ID'),
        'client_secret': current_app.config.get('GITHUB_CLIENT_SECRET'),
        'code': code,
        'redirect_uri': redirect_uri
    }

    token_response = requests.post(
        token_url,
        data=token_data,
        headers={'Accept': 'application/json'}
    )

    if not token_response.ok:
        flash('Erreur lors de la connexion avec GitHub.', 'danger')
        return redirect(url_for('main.login'))

    tokens = token_response.json()
    access_token = tokens.get('access_token')

    # --- Récupérer les infos utilisateur ---
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    user_response = requests.get('https://api.github.com/user', headers=headers)

    if not user_response.ok:
        flash('Erreur lors de la récupération des informations GitHub.', 'danger')
        return redirect(url_for('main.login'))

    github_user = user_response.json()

    github_id = str(github_user.get('id'))
    username = github_user.get('login')
    name = github_user.get('name', '') or username
    avatar_url = github_user.get('avatar_url', '')
    bio = github_user.get('bio', '')
    location = github_user.get('location', '')
    company = github_user.get('company', '')
    blog = github_user.get('blog', '')

    # Email (peut être privé)
    email_response = requests.get('https://api.github.com/user/emails', headers=headers)
    email = None

    if email_response.ok:
        emails = email_response.json()
        for e in emails:
            if e.get('primary') and e.get('verified'):
                email = e.get('email')
                break
        if not email and emails:
            email = emails[0].get('email')

    if not email:
        flash('Impossible de récupérer votre email GitHub.', 'danger')
        return redirect(url_for('main.login'))

    # --- Vérifier si l'utilisateur existe ---
    user = User.query.filter_by(github_id=github_id).first()

    if not user:
        user = User.query.filter_by(email=email).first()

        if user:
            # Lier le compte GitHub
            user.github_id = github_id
            if avatar_url and not user.avatar:
                user.avatar = avatar_url
            if bio and not user.bio:
                user.bio = bio
            if not user.github_url:
                user.github_url = f"https://github.com/{username}"
            db.session.commit()
        else:
            # Créer un nouvel utilisateur
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                display_name=name,
                github_id=github_id,
                avatar=avatar_url or 'default-avatar.png',
                bio=bio,
                location=location,
                github_url=f"https://github.com/{username}",
                website_url=blog,
                headline=company,
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()

    # --- Connexion ---
    session['user_id'] = user.id
    session['username'] = user.username
    user.last_login = db.func.now()
    db.session.commit()

    flash(f'Bienvenue, {user.display_name or user.username} !', 'success')
    return redirect(url_for('main.index'))


# ============================================
# PROFILS UTILISATEURS
# ============================================
@main_bp.route('/u/<username>')
def profile(username):
    """Profil public d'un utilisateur"""
    profile_user = User.query.filter_by(username=username).first_or_404()
    current_user = get_current_user()

    # Posts du profil
    posts = profile_user.posts.order_by(Post.created_at.desc()).limit(10).all()

    # Projets
    projects = profile_user.owned_projects.order_by(Project.created_at.desc()).limit(6).all()

    # Vérifier si on suit cet utilisateur
    is_following = False
    if current_user:
        is_following = current_user.is_following(profile_user)

    return render_template('profile.html',
                         profile_user=profile_user,
                         posts=posts,
                         projects=projects,
                         is_following=is_following,
                         user=current_user)


@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Édition du profil"""
    user = get_current_user()

    if request.method == 'POST':
        user.display_name = request.form.get('display_name', '').strip() or user.display_name
        user.headline = request.form.get('headline', '').strip()
        user.bio = request.form.get('bio', '').strip()
        user.location = request.form.get('location', '').strip()
        user.role = request.form.get('role', user.role)
        user.experience_level = request.form.get('experience_level', user.experience_level)
        user.github_url = request.form.get('github_url', '').strip()
        user.linkedin_url = request.form.get('linkedin_url', '').strip()
        user.portfolio_url = request.form.get('portfolio_url', '').strip()
        user.twitter_url = request.form.get('twitter_url', '').strip()
        user.website_url = request.form.get('website_url', '').strip()
        user.is_available = request.form.get('is_available') == 'on'
        user.availability_status = request.form.get('availability_status', 'not_available')

        # Gestion de l'avatar (upload)
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file.filename:
                filename = secure_filename(f"avatar_{user.id}_{avatar_file.filename}")
                avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                avatar_file.save(avatar_path)
                user.avatar = filename

        db.session.commit()
        flash('Profil mis à jour avec succès !', 'success')
        return redirect(url_for('main.profile', username=user.username))

    return render_template('edit_profile.html', user=user)


@main_bp.route('/profile/settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    """Paramètres du compte"""
    user = get_current_user()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not check_password_hash(user.password_hash, current_password):
                flash('Mot de passe actuel incorrect.', 'danger')
            elif len(new_password) < 8:
                flash('Le nouveau mot de passe doit faire au moins 8 caractères.', 'danger')
            elif new_password != confirm_password:
                flash('Les mots de passe ne correspondent pas.', 'danger')
            else:
                user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash('Mot de passe mis à jour.', 'success')

        elif action == 'update_email':
            new_email = request.form.get('email', '').strip().lower()
            if User.query.filter_by(email=new_email).first() and new_email != user.email:
                flash('Cet email est déjà utilisé.', 'danger')
            else:
                user.email = new_email
                db.session.commit()
                flash('Email mis à jour.', 'success')

    return render_template('profile_settings.html', user=user)


# ============================================
# FOLLOW / UNFOLLOW
# ============================================
@main_bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    """Suivre un utilisateur"""
    current_user = get_current_user()
    user_to_follow = User.query.filter_by(username=username).first_or_404()

    if current_user.id == user_to_follow.id:
        flash("Vous ne pouvez pas vous suivre vous-même.", 'warning')
        return redirect(url_for('main.profile', username=username))

    if current_user.follow(user_to_follow):
        # Créer une notification
        notif = Notification(
            user_id=user_to_follow.id,
            notification_type='follow',
            title='Nouveau follower',
            message=f'{current_user.display_name or current_user.username} vous suit maintenant.',
            actor_id=current_user.id
        )
        db.session.add(notif)
        flash(f'Vous suivez maintenant {user_to_follow.display_name or username}.', 'success')
    else:
        flash(f'Vous suivez déjà {user_to_follow.display_name or username}.', 'info')

    return redirect(url_for('main.profile', username=username))


@main_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    """Ne plus suivre un utilisateur"""
    current_user = get_current_user()
    user_to_unfollow = User.query.filter_by(username=username).first_or_404()

    if current_user.unfollow(user_to_unfollow):
        flash(f'Vous ne suivez plus {user_to_unfollow.display_name or username}.', 'info')
    else:
        flash(f'Vous ne suiviez pas {user_to_unfollow.display_name or username}.', 'warning')

    return redirect(url_for('main.profile', username=username))


@main_bp.route('/u/<username>/followers')
def followers(username):
    """Liste des followers"""
    profile_user = User.query.filter_by(username=username).first_or_404()
    followers_list = profile_user.followers.all()
    return render_template('followers.html', profile_user=profile_user, 
                         followers=followers_list, user=get_current_user())


@main_bp.route('/u/<username>/following')
def following(username):
    """Liste des suivis"""
    profile_user = User.query.filter_by(username=username).first_or_404()
    following_list = profile_user.following.all()
    return render_template('following.html', profile_user=profile_user,
                         following=following_list, user=get_current_user())


# ============================================
# POSTS
# ============================================
@main_bp.route('/post/<int:post_id>')
def post_detail(post_id):
    """Détail d'un post"""
    post = Post.query.get_or_404(post_id)
    comments = post.comments.order_by(Comment.created_at.desc()).all()
    return render_template('post_detail.html', post=post, comments=comments, user=get_current_user())


@main_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    """Créer un nouveau post"""
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        post_type = request.form.get('post_type', 'article')

        if not content:
            flash('Le contenu ne peut pas être vide.', 'danger')
            return render_template('create_post.html', user=get_current_user())

        new_post = Post(
            content=content,
            post_type=post_type,
            user_id=get_current_user().id
        )

        # Gestion de l'image
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename:
                filename = secure_filename(f"post_{get_current_user().id}_{image_file.filename}")
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)
                new_post.image_url = filename

        # Tags
        tags_raw = request.form.get('tags', '')
        if tags_raw:
            tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(slug=tag_name.lower()).first()
                if not tag:
                    tag = Tag(name=tag_name.capitalize(), slug=tag_name.lower())
                    db.session.add(tag)
                new_post.tags.append(tag)

        db.session.add(new_post)

        # Mettre à jour le compteur de posts
        user = get_current_user()
        user.posts_count += 1

        db.session.commit()
        flash('Post publié avec succès !', 'success')
        return redirect(url_for('main.index'))

    return render_template('create_post.html', user=get_current_user())


@main_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Éditer un post"""
    post = Post.query.get_or_404(post_id)
    user = get_current_user()

    if post.user_id != user.id and not user.is_admin:
        abort(403)

    if request.method == 'POST':
        post.content = request.form.get('content', '').strip()
        post.post_type = request.form.get('post_type', post.post_type)

        # Mise à jour des tags
        post.tags.clear()
        tags_raw = request.form.get('tags', '')
        if tags_raw:
            tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(slug=tag_name.lower()).first()
                if not tag:
                    tag = Tag(name=tag_name.capitalize(), slug=tag_name.lower())
                    db.session.add(tag)
                post.tags.append(tag)

        db.session.commit()
        flash('Post mis à jour.', 'success')
        return redirect(url_for('main.post_detail', post_id=post.id))

    return render_template('edit_post.html', post=post, user=user)


@main_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """Supprimer un post"""
    post = Post.query.get_or_404(post_id)
    user = get_current_user()

    if post.user_id != user.id and not user.is_admin:
        abort(403)

    user.posts_count -= 1
    db.session.delete(post)
    db.session.commit()

    flash('Post supprimé.', 'info')
    return redirect(url_for('main.index'))


# ============================================
# COMMENTAIRES
# ============================================
@main_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Ajouter un commentaire"""
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()

    if not content:
        flash('Le commentaire ne peut pas être vide.', 'danger')
        return redirect(url_for('main.post_detail', post_id=post_id))

    comment = Comment(
        content=content,
        user_id=get_current_user().id,
        post_id=post_id
    )

    db.session.add(comment)

    # Notification à l'auteur du post
    if post.user_id != get_current_user().id:
        notif = Notification(
            user_id=post.user_id,
            notification_type='comment',
            title='Nouveau commentaire',
            message=f'{get_current_user().display_name or get_current_user().username} a commenté votre post.',
            actor_id=get_current_user().id,
            post_id=post.id
        )
        db.session.add(notif)

    db.session.commit()
    flash('Commentaire ajouté.', 'success')
    return redirect(url_for('main.post_detail', post_id=post_id))


# ============================================
# API - FEED (AJAX - Scroll Infini)
# ============================================
@main_bp.route('/api/feed')
def api_feed():
    """Retourne les posts en JSON pour le scroll infini"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    post_type = request.args.get('type', 'all')

    user = get_current_user()

    if user:
        posts_query = user.get_feed_posts()
    else:
        posts_query = Post.query.order_by(Post.created_at.desc())

    # Filtre par type
    if post_type != 'all':
        posts_query = posts_query.filter_by(post_type=post_type)

    # Pagination
    paginated = posts_query.paginate(page=page, per_page=per_page, error_out=False)

    posts_data = []
    for post in paginated.items:
        posts_data.append({
            'id': post.id,
            'author': {
                'username': post.author.username,
                'display_name': post.author.display_name or post.author.username,
                'avatar': post.author.avatar,
                'role': post.author.role
            },
            'content': post.content,
            'excerpt': post.excerpt or (post.content[:160] + '...' if len(post.content) > 160 else post.content),
            'post_type': post.post_type,
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'views_count': post.views_count,
            'created_at': post.created_at.strftime('%d %b'),
            'cover_image': post.cover_image,
            'tags': [{'name': tag.name, 'slug': tag.slug} for tag in post.tags[:3]]
        })

    return jsonify({
        'posts': posts_data,
        'has_next': paginated.has_next,
        'has_prev': paginated.has_prev,
        'current_page': paginated.page,
        'total_pages': paginated.pages
    })


# ============================================
# API - LIKE / UNLIKE
# ============================================
@main_bp.route('/api/posts/<int:post_id>/like', methods=['POST'])
@login_required
def api_like_post(post_id):
    """Like ou unlike un post via AJAX"""
    user = get_current_user()
    post = Post.query.get_or_404(post_id)

    if user.has_liked_post(post):
        user.unlike_post(post)
        liked = False
    else:
        user.like_post(post)
        liked = True

        # Notification
        if post.user_id != user.id:
            notif = Notification(
                user_id=post.user_id,
                notification_type='like',
                title='Nouveau like',
                message=f'{user.display_name or user.username} a aimé votre post.',
                actor_id=user.id,
                post_id=post.id
            )
            db.session.add(notif)

    return jsonify({
        'liked': liked,
        'likes_count': post.likes_count
    })


# ============================================
# API - COMMENTAIRES
# ============================================
@main_bp.route('/api/posts/<int:post_id>/comments')
def api_post_comments(post_id):
    """Récupérer les commentaires d'un post en JSON"""
    post = Post.query.get_or_404(post_id)
    comments = post.comments.order_by(Comment.created_at.desc()).all()

    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'author': {
                'username': comment.author.username,
                'display_name': comment.author.display_name or comment.author.username,
                'avatar': comment.author.avatar
            },
            'created_at': comment.created_at.strftime('%d %b %H:%M'),
            'likes_count': comment.likes_count
        })

    return jsonify({'comments': comments_data})


# ============================================
# NOTIFICATIONS
# ============================================
@main_bp.route('/notifications')
@login_required
def notifications():
    """Centre de notifications"""
    user = get_current_user()
    notifs = user.notifications.order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notifs, user=user)


@main_bp.route('/api/notifications/unread-count')
@login_required
def api_unread_notifications_count():
    """Compteur de notifications non lues"""
    user = get_current_user()
    count = user.notifications.filter_by(is_read=False).count()
    return jsonify({'count': count})


@main_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marquer une notification comme lue"""
    user = get_current_user()
    notif = Notification.query.get_or_404(notification_id)

    if notif.user_id != user.id:
        return jsonify({'error': 'Non autorisé'}), 403

    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})


@main_bp.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Marquer toutes les notifications comme lues"""
    user = get_current_user()
    user.notifications.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})


# ============================================
# PROJETS
# ============================================
@main_bp.route('/projects')
def projects():
    """Explorer les projets"""
    page = request.args.get('page', 1, type=int)
    projects_query = Project.query.order_by(Project.created_at.desc())
    paginated = projects_query.paginate(page=page, per_page=12, error_out=False)
    return render_template('projects.html', projects=paginated, user=get_current_user())


@main_bp.route('/project/<slug>')
def project_detail(slug):
    """Détail d'un projet"""
    project = Project.query.filter_by(slug=slug).first_or_404()
    is_member = False
    user = get_current_user()
    if user:
        is_member = user in project.members
    return render_template('project_detail.html', project=project, is_member=is_member, user=user)


@main_bp.route('/project/new', methods=['GET', 'POST'])
@login_required
def create_project():
    """Créer un nouveau projet"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        slug = request.form.get('slug', '').strip().lower()

        if not name or not description or not slug:
            flash('Tous les champs obligatoires doivent être remplis.', 'danger')
            return render_template('create_project.html', user=get_current_user())

        # Vérifier unicité du slug
        if Project.query.filter_by(slug=slug).first():
            flash('Ce slug est déjà utilisé.', 'danger')
            return render_template('create_project.html', user=get_current_user())

        project = Project(
            name=name,
            slug=slug,
            description=description,
            short_description=request.form.get('short_description', '').strip(),
            github_url=request.form.get('github_url', '').strip(),
            demo_url=request.form.get('demo_url', '').strip(),
            tech_stack=request.form.getlist('tech_stack'),
            owner_id=get_current_user().id
        )

        db.session.add(project)

        # Le créateur est automatiquement membre
        get_current_user().projects.append(project)
        get_current_user().projects_count += 1

        db.session.commit()
        flash('Projet créé avec succès !', 'success')
        return redirect(url_for('main.project_detail', slug=slug))

    return render_template('create_project.html', user=get_current_user())


@main_bp.route('/project/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(slug):
    """Éditer un projet"""
    project = Project.query.filter_by(slug=slug).first_or_404()
    user = get_current_user()

    if project.owner_id != user.id and not user.is_admin:
        abort(403)

    if request.method == 'POST':
        project.name = request.form.get('name', project.name).strip()
        project.description = request.form.get('description', '').strip()
        project.short_description = request.form.get('short_description', '').strip()
        project.github_url = request.form.get('github_url', '').strip()
        project.demo_url = request.form.get('demo_url', '').strip()
        project.status = request.form.get('status', project.status)
        project.is_open_source = request.form.get('is_open_source') == 'on'

        db.session.commit()
        flash('Projet mis à jour.', 'success')
        return redirect(url_for('main.project_detail', slug=slug))

    return render_template('edit_project.html', project=project, user=user)


@main_bp.route('/api/projects/<int:project_id>/like', methods=['POST'])
@login_required
def api_like_project(project_id):
    """Like ou unlike un projet"""
    user = get_current_user()
    project = Project.query.get_or_404(project_id)

    if user.has_liked_project(project):
        user.unlike_project(project)
        liked = False
    else:
        user.like_project(project)
        liked = True

    return jsonify({
        'liked': liked,
        'likes_count': project.likes_count
    })


# ============================================
# SNIPPETS DE CODE
# ============================================
@main_bp.route('/snippets')
def snippets():
    """Bibliothèque de snippets"""
    page = request.args.get('page', 1, type=int)
    language = request.args.get('language', '')

    query = CodeSnippet.query
    if language:
        query = query.filter_by(language=language)

    paginated = query.order_by(CodeSnippet.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('snippets.html', snippets=paginated, user=get_current_user(), 
                         current_language=language)


@main_bp.route('/snippet/<int:snippet_id>')
def snippet_detail(snippet_id):
    """Détail d'un snippet"""
    snippet = CodeSnippet.query.get_or_404(snippet_id)
    return render_template('snippet_detail.html', snippet=snippet, user=get_current_user())


@main_bp.route('/snippet/new', methods=['GET', 'POST'])
@login_required
def create_snippet():
    """Créer un snippet de code"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        code = request.form.get('code', '').strip()
        language = request.form.get('language', '').strip()
        description = request.form.get('description', '').strip()

        if not title or not code or not language:
            flash('Titre, code et langage sont obligatoires.', 'danger')
            return render_template('create_snippet.html', user=get_current_user())

        snippet = CodeSnippet(
            title=title,
            code=code,
            language=language,
            description=description,
            user_id=get_current_user().id
        )

        db.session.add(snippet)
        db.session.commit()
        flash('Snippet publié !', 'success')
        return redirect(url_for('main.snippets'))

    return render_template('create_snippet.html', user=get_current_user())


# ============================================
# MESSAGERIE
# ============================================
@main_bp.route('/messages')
@login_required
def messages():
    """Liste des conversations"""
    user = get_current_user()

    # Récupérer les conversations (dernier message par contact)
    sent = Message.query.filter_by(sender_id=user.id).order_by(Message.created_at.desc()).all()
    received = Message.query.filter_by(recipient_id=user.id).order_by(Message.created_at.desc()).all()

    conversations = {}
    for msg in sent + received:
        other_id = msg.recipient_id if msg.sender_id == user.id else msg.sender_id
        if other_id not in conversations:
            conversations[other_id] = msg

    return render_template('messages.html', conversations=conversations.values(), user=user)


@main_bp.route('/messages/<username>')
@login_required
def chat(username):
    """Conversation avec un utilisateur"""
    user = get_current_user()
    other = User.query.filter_by(username=username).first_or_404()

    # Marquer les messages comme lus
    Message.query.filter_by(sender_id=other.id, recipient_id=user.id, is_read=False).update({'is_read': True})
    db.session.commit()

    # Récupérer les messages
    msgs = Message.query.filter(
        ((Message.sender_id == user.id) & (Message.recipient_id == other.id)) |
        ((Message.sender_id == other.id) & (Message.recipient_id == user.id))
    ).order_by(Message.created_at.asc()).all()

    return render_template('chat.html', messages=msgs, other=other, user=user)


@main_bp.route('/messages/<username>/send', methods=['POST'])
@login_required
def send_message(username):
    """Envoyer un message"""
    user = get_current_user()
    other = User.query.filter_by(username=username).first_or_404()
    content = request.form.get('content', '').strip()

    if not content:
        flash('Le message ne peut pas être vide.', 'danger')
        return redirect(url_for('main.chat', username=username))

    msg = Message(
        content=content,
        sender_id=user.id,
        recipient_id=other.id
    )

    db.session.add(msg)
    db.session.commit()

    return redirect(url_for('main.chat', username=username))


@main_bp.route('/api/messages/unread')
@login_required
def api_unread_messages():
    """Messages non lus"""
    user = get_current_user()
    count = Message.query.filter_by(recipient_id=user.id, is_read=False).count()
    return jsonify({'count': count})


# ============================================
# JOBS / OFFRES D'EMPLOI
# ============================================
@main_bp.route('/jobs')
def jobs():
    """Liste des offres d'emploi"""
    page = request.args.get('page', 1, type=int)
    location_type = request.args.get('location_type', '')

    query = Job.query.filter_by(status='active').order_by(Job.created_at.desc())
    if location_type:
        query = query.filter_by(location_type=location_type)

    paginated = query.paginate(page=page, per_page=10, error_out=False)
    return render_template('jobs.html', jobs=paginated, user=get_current_user(), 
                         location_type=location_type)


@main_bp.route('/job/<int:job_id>')
def job_detail(job_id):
    """Détail d'une offre"""
    job = Job.query.get_or_404(job_id)
    has_applied = False
    user = get_current_user()
    if user:
        has_applied = JobApplication.query.filter_by(job_id=job_id, applicant_id=user.id).first() is not None
    return render_template('job_detail.html', job=job, has_applied=has_applied, user=user)


@main_bp.route('/job/new', methods=['GET', 'POST'])
@login_required
def create_job():
    """Publier une offre d'emploi"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        company_name = request.form.get('company_name', '').strip()
        description = request.form.get('description', '').strip()

        if not title or not company_name or not description:
            flash('Tous les champs obligatoires doivent être remplis.', 'danger')
            return render_template('create_job.html', user=get_current_user())

        job = Job(
            title=title,
            company_name=company_name,
            description=description,
            requirements=request.form.getlist('requirements'),
            job_type=request.form.get('job_type', 'full_time'),
            location_type=request.form.get('location_type', 'remote'),
            location=request.form.get('location', '').strip(),
            salary_range=request.form.get('salary_range', '').strip(),
            tech_stack=request.form.getlist('tech_stack'),
            poster_id=get_current_user().id
        )

        db.session.add(job)
        db.session.commit()
        flash('Offre publiée avec succès !', 'success')
        return redirect(url_for('main.jobs'))

    return render_template('create_job.html', user=get_current_user())


@main_bp.route('/job/<int:job_id>/apply', methods=['POST'])
@login_required
def apply_job(job_id):
    """Postuler à une offre"""
    job = Job.query.get_or_404(job_id)
    user = get_current_user()

    # Vérifier si déjà postulé
    existing = JobApplication.query.filter_by(job_id=job_id, applicant_id=user.id).first()
    if existing:
        flash('Vous avez déjà postulé à cette offre.', 'info')
        return redirect(url_for('main.job_detail', job_id=job_id))

    application = JobApplication(
        cover_letter=request.form.get('cover_letter', '').strip(),
        resume_url=request.form.get('resume_url', '').strip(),
        portfolio_url=request.form.get('portfolio_url', '').strip(),
        applicant_id=user.id,
        job_id=job_id
    )

    db.session.add(application)
    job.applications_count += 1
    db.session.commit()

    # Notification au recruteur
    notif = Notification(
        user_id=job.poster_id,
        notification_type='job_match',
        title='Nouvelle candidature',
        message=f'{user.display_name or user.username} a postulé à {job.title}.',
        actor_id=user.id
    )
    db.session.add(notif)
    db.session.commit()

    flash('Candidature envoyée !', 'success')
    return redirect(url_for('main.job_detail', job_id=job_id))


@main_bp.route('/jobs/applications')
@login_required
def my_applications():
    """Mes candidatures"""
    user = get_current_user()
    applications = user.applications.order_by(JobApplication.created_at.desc()).all()
    return render_template('my_applications.html', applications=applications, user=user)


@main_bp.route('/jobs/posted')
@login_required
def my_jobs():
    """Mes offres publiées"""
    user = get_current_user()
    jobs = user.jobs_posted.order_by(Job.created_at.desc()).all()
    return render_template('my_jobs.html', jobs=jobs, user=user)


# ============================================
# EXPLORER & RECHERCHE
# ============================================
@main_bp.route('/explore')
def explore():
    """Page explorer"""
    # Posts populaires
    popular_posts = Post.query.order_by(Post.likes_count.desc()).limit(10).all()
    # Projets tendance
    trending_projects = Project.query.order_by(Project.likes_count.desc()).limit(6).all()
    # Tags populaires
    popular_tags = Tag.query.order_by(Tag.posts_count.desc()).limit(10).all()

    return render_template('explore.html',
                         popular_posts=popular_posts,
                         trending_projects=trending_projects,
                         popular_tags=popular_tags,
                         user=get_current_user())


@main_bp.route('/search')
def search():
    """Recherche globale"""
    q = request.args.get('q', '').strip()
    if not q:
        return render_template('search.html', results=None, query='', user=get_current_user())

    # Recherche dans les utilisateurs
    users = User.query.filter(
        (User.username.ilike(f'%{q}%')) |
        (User.display_name.ilike(f'%{q}%')) |
        (User.bio.ilike(f'%{q}%'))
    ).limit(10).all()

    # Recherche dans les posts
    posts = Post.query.filter(Post.content.ilike(f'%{q}%')).order_by(Post.created_at.desc()).limit(10).all()

    # Recherche dans les projets
    projects = Project.query.filter(
        (Project.name.ilike(f'%{q}%')) |
        (Project.description.ilike(f'%{q}%'))
    ).limit(10).all()

    # Recherche dans les tags
    tags = Tag.query.filter(
        (Tag.name.ilike(f'%{q}%')) |
        (Tag.slug.ilike(f'%{q}%'))
    ).limit(10).all()

    return render_template('search.html',
                         results={
                             'users': users,
                             'posts': posts,
                             'projects': projects,
                             'tags': tags
                         },
                         query=q,
                         user=get_current_user())


@main_bp.route('/tags/<slug>')
def tag_detail(slug):
    """Posts et projets par tag"""
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    posts = tag.posts.order_by(Post.created_at.desc()).limit(20).all()
    projects = tag.projects.order_by(Project.created_at.desc()).limit(10).all()
    return render_template('tag_detail.html', tag=tag, posts=posts, projects=projects, user=get_current_user())


@main_bp.route('/trending')
def trending():
    """Contenu tendance"""
    # Posts les plus aimés cette semaine
    trending_posts = Post.query.order_by(Post.likes_count.desc()).limit(20).all()
    trending_projects = Project.query.order_by(Project.likes_count.desc()).limit(10).all()

    return render_template('trending.html',
                         posts=trending_posts,
                         projects=trending_projects,
                         user=get_current_user())


# ============================================
# PAGES STATIQUES
# ============================================
@main_bp.route('/about')
def about():
    """À propos"""
    return render_template('about.html', user=get_current_user())


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash('Tous les champs sont obligatoires.', 'danger')
        else:
            flash('Message envoyé ! Nous vous répondrons rapidement.', 'success')
            return redirect(url_for('main.contact'))

    return render_template('contact.html', user=get_current_user())


@main_bp.route('/terms')
def terms():
    """Conditions d'utilisation"""
    return render_template('terms.html', user=get_current_user())


@main_bp.route('/privacy')
def privacy():
    """Politique de confidentialité"""
    return render_template('privacy.html', user=get_current_user())


@main_bp.route('/help')
def help_page():
    """Aide / FAQ"""
    return render_template('help.html', user=get_current_user())