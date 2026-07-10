from db import db
from datetime import datetime, timedelta


# ============================================
# TABLE DE JONCTION : Followers
# ============================================
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


# ============================================
# TABLE DE JONCTION : Membres d'équipe
# ============================================
project_members = db.Table('project_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('role', db.String(50), default='contributor'),  # owner, contributor, reviewer
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)


# ============================================
# TABLE DE JONCTION : Likes sur posts
# ============================================
post_likes = db.Table('post_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


# ============================================
# TABLE DE JONCTION : Likes sur projets
# ============================================
project_likes = db.Table('project_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


# ============================================
# TABLE DE JONCTION : Tags tech
# ============================================
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

project_tags = db.Table('project_tags',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

user_skills = db.Table('user_skills',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


# ============================================
# UTILISATEUR (Développeur / Tech)
# ============================================
class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # --- Identifiants ---
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    
    # --- Profil Tech ---
    display_name = db.Column(db.String(100))
    bio = db.Column(db.Text)  # Présentation tech
    headline = db.Column(db.String(200))  # "Full-Stack Dev | React & Python"
    
    # Avatars
    avatar = db.Column(db.String(500), default='default-avatar.png')
    banner = db.Column(db.String(500), default='default-banner.png')
    
    # --- Liens externes (Dev profiles) ---
    github_url = db.Column(db.String(500))
    linkedin_url = db.Column(db.String(500))
    portfolio_url = db.Column(db.String(500))
    twitter_url = db.Column(db.String(500))
    website_url = db.Column(db.String(500))
    
    # --- Localisation & Disponibilité ---
    location = db.Column(db.String(100))
    is_available = db.Column(db.Boolean, default=False)  # Open to work/collab
    availability_status = db.Column(db.String(50), default='not_available')  
    # not_available, open_to_work, open_to_collaborate, hiring
    
    # --- Métriques ---
    reputation_score = db.Column(db.Integer, default=0)  # Points de réputation
    followers_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    posts_count = db.Column(db.Integer, default=0)
    projects_count = db.Column(db.Integer, default=0)
    
    # --- Niveau & Rôles ---
    role = db.Column(db.String(50), default='developer')  
    # developer, designer, product_manager, data_scientist, devops, etc.
    experience_level = db.Column(db.String(50), default='junior')
    # junior, mid, senior, lead, principal
    
    # --- OAuth ---
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    github_id = db.Column(db.String(100), unique=True, nullable=True)
    
    # --- Sécurité ---
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # --- Timestamps ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # ============================================
    # RELATIONS
    # ============================================
    
    # Posts
    posts = db.relationship('Post', backref='author', lazy='dynamic',
                          foreign_keys='Post.user_id', cascade='all, delete-orphan')
    
    # Projets (dont il est propriétaire)
    owned_projects = db.relationship('Project', backref='owner', lazy='dynamic',
                                      foreign_keys='Project.owner_id',
                                      cascade='all, delete-orphan')
    
    # Projets auxquels il contribue
    projects = db.relationship('Project', secondary=project_members, backref='members')
    
    # Commentaires
    comments = db.relationship('Comment', backref='author', lazy='dynamic',
                               cascade='all, delete-orphan')
    
    # Snippets de code
    snippets = db.relationship('CodeSnippet', backref='author', lazy='dynamic',
                                cascade='all, delete-orphan')
    
    # Messages
    messages_sent = db.relationship('Message', backref='sender', lazy='dynamic',
                                    foreign_keys='Message.sender_id',
                                    cascade='all, delete-orphan')
    messages_received = db.relationship('Message', backref='recipient', lazy='dynamic',
                                         foreign_keys='Message.recipient_id')
    
    # Followers
    followers = db.relationship('User', secondary=followers,
                                primaryjoin=(followers.c.followed_id == id),
                                secondaryjoin=(followers.c.follower_id == id),
                                backref=db.backref('following', lazy='dynamic'),
                                lazy='dynamic')
    
    # Likes
    liked_posts = db.relationship('Post', secondary=post_likes, backref='likers', lazy='dynamic')
    liked_projects = db.relationship('Project', secondary=project_likes, backref='likers', lazy='dynamic')
    
    # Skills (tags tech)
    skills = db.relationship('Tag', secondary=user_skills, backref='skilled_users')
    
    # Notifications
    notifications = db.relationship(
        'Notification',
        foreign_keys='Notification.user_id',
        backref=db.backref('user', foreign_keys='Notification.user_id', uselist=False),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # Jobs publiés (si recruteur)
    jobs_posted = db.relationship('Job', backref='poster', lazy='dynamic',
                                   foreign_keys='Job.poster_id',
                                   cascade='all, delete-orphan')
    
    # Candidatures
    applications = db.relationship('JobApplication', backref='applicant', lazy='dynamic',
                                    cascade='all, delete-orphan')
    
    # ============================================
    # MÉTHODES
    # ============================================
    
    def follow(self, user):
        if not self.is_following(user):
            self.following.append(user)
            self.following_count += 1
            user.followers_count += 1
            db.session.commit()
            return True
        return False
    
    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)
            self.following_count -= 1
            user.followers_count -= 1
            db.session.commit()
            return True
        return False
    
    def is_following(self, user):
        return self.following.filter(followers.c.followed_id == user.id).first() is not None
    
    def like_post(self, post):
        if not self.has_liked_post(post):
            self.liked_posts.append(post)
            post.likes_count += 1
            db.session.commit()
            return True
        return False
    
    def unlike_post(self, post):
        if self.has_liked_post(post):
            self.liked_posts.remove(post)
            post.likes_count -= 1
            db.session.commit()
            return True
        return False
    
    def has_liked_post(self, post):
        return self.liked_posts.filter(post_likes.c.post_id == post.id).first() is not None
    
    def like_project(self, project):
        if not self.has_liked_project(project):
            self.liked_projects.append(project)
            project.likes_count += 1
            db.session.commit()
            return True
        return False
    
    def unlike_project(self, project):
        if self.has_liked_project(project):
            self.liked_projects.remove(project)
            project.likes_count -= 1
            db.session.commit()
            return True
        return False
    
    def has_liked_project(self, project):
        return self.liked_projects.filter(project_likes.c.project_id == project.id).first() is not None
    
    def get_feed_posts(self):
        """Feed : posts des utilisateurs suivis + posts tech populaires"""
        followed_posts = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)
        own_posts = Post.query.filter_by(user_id=self.id)
        return followed_posts.union(own_posts).order_by(Post.created_at.desc())
    
    def __repr__(self):
        return f'<User {self.username}>'


# ============================================
# POST (Publication tech)
# ============================================
class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)

    # Contenu
    content = db.Column(db.Text, nullable=False)

    # Type de post (VRAI CHAMP, pas une property)
    post_type = db.Column(db.String(50), default='article')
    # article, tutorial, question, show_and_tell, project

    # Média
    image_url = db.Column(db.String(500))

    # Métriques
    likes_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Clé étrangère
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # ============================================
    # RELATIONS
    # ============================================

    comments = db.relationship('Comment', backref='post', lazy='dynamic',
                                cascade='all, delete-orphan')

    tags = db.relationship('Tag', secondary=post_tags, backref='posts')

    # ============================================
    # PROPERTIES (calculées uniquement)
    # ============================================

    @property
    def title(self):
        """Génère un titre à partir du contenu"""
        if self.content and len(self.content) > 80:
            return self.content[:80] + '…'
        return self.content or 'Publication'

    @property
    def excerpt(self):
        """Génère un extrait à partir du contenu"""
        if self.content and len(self.content) > 160:
            return self.content[:160] + '…'
        return self.content

    @property
    def cover_image(self):
        """Alias pour image_url"""
        return self.image_url

    @property
    def status(self):
        """Tous les posts sont publiés par défaut"""
        return 'published'

    @property
    def comments_count(self):
        """Compte les commentaires"""
        return self.comments.count()

    @property
    def views_count(self):
        """À implémenter plus tard"""
        return 0

    def __repr__(self):
        return f'<Post {self.id}>'


# ============================================
# PROJET (Showcase de projets tech)
# ============================================
class Project(db.Model):
    __tablename__ = 'project'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300))
    
    # Liens
    github_url = db.Column(db.String(500))
    demo_url = db.Column(db.String(500))
    documentation_url = db.Column(db.String(500))
    
    # Média
    cover_image = db.Column(db.String(500))
    screenshots = db.Column(db.JSON)  # Liste d'URLs
    
    # Tech stack
    tech_stack = db.Column(db.JSON)  # ["Python", "Flask", "React", "PostgreSQL"]
    
    # Statut
    status = db.Column(db.String(50), default='in_progress')
    # in_progress, completed, maintenance, abandoned
    
    # Métriques
    likes_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    # Open source ?
    is_open_source = db.Column(db.Boolean, default=True)
    license = db.Column(db.String(100))  # MIT, GPL, Apache, etc.
    
    # Recherche de contributeurs
    looking_for_contributors = db.Column(db.Boolean, default=False)
    contributors_needed = db.Column(db.JSON)  # ["frontend", "backend", "design"]
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clés étrangères
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # ============================================
    # RELATIONS
    # ============================================
    
    tags = db.relationship('Tag', secondary=project_tags, backref='projects')
    
    def __repr__(self):
        return f'<Project {self.name}>'


# ============================================
# SNIPPET DE CODE
# ============================================
class CodeSnippet(db.Model):
    __tablename__ = 'code_snippet'
    
    id = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Code
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)  # python, javascript, rust, etc.
    
    # Métriques
    likes_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clé étrangère
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<CodeSnippet {self.title}>'


# ============================================
# TAG (Technologies / Catégories)
# ============================================
class Tag(db.Model):
    __tablename__ = 'tag'
    
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    
    # Catégorie
    category = db.Column(db.String(50), default='language')
    # language, framework, tool, topic, role
    
    # Description
    description = db.Column(db.Text)
    
    # Métriques
    posts_count = db.Column(db.Integer, default=0)
    projects_count = db.Column(db.Integer, default=0)
    users_count = db.Column(db.Integer, default=0)
    
    # Couleur pour l'UI
    color = db.Column(db.String(7), default='#6366f1')  # Hex color
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.name}>'


# ============================================
# COMMENTAIRE
# ============================================
class Comment(db.Model):
    __tablename__ = 'comment'
    
    id = db.Column(db.Integer, primary_key=True)
    
    content = db.Column(db.Text, nullable=False)
    
    # Métriques
    likes_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clés étrangères
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    # Réponses imbriquées
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
                             lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Comment {self.id}>'


# ============================================
# MESSAGE (Chat privé)
# ============================================
class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, code, image
    
    # Code attaché
    code_snippet = db.Column(db.Text)
    code_language = db.Column(db.String(50))
    
    # Statut
    is_read = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Clés étrangères
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Message {self.id}>'


# ============================================
# NOTIFICATION
# ============================================
class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    
    notification_type = db.Column(db.String(50), nullable=False)
    # Types : like, comment, follow, mention, project_invite, job_match, message
    
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    link = db.Column(db.String(500))
    
    # IDs des ressources
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    
    # Statut
    is_read = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clé étrangère
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Notification {self.notification_type}>'


# ============================================
# JOB (Offre d'emploi tech)
# ============================================
class Job(db.Model):
    __tablename__ = 'job'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations
    title = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    company_logo = db.Column(db.String(500))
    
    # Description
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.JSON)  # Liste de compétences requises
    responsibilities = db.Column(db.JSON)
    
    # Détails
    job_type = db.Column(db.String(50), default='full_time')
    # full_time, part_time, contract, freelance, internship
    
    location_type = db.Column(db.String(50), default='remote')
    # remote, on_site, hybrid
    
    location = db.Column(db.String(100))
    salary_range = db.Column(db.String(100))  # "$80k - $120k"
    
    # Tech stack
    tech_stack = db.Column(db.JSON)
    
    # Statut
    status = db.Column(db.String(50), default='active')
    # active, closed, draft
    
    # Métriques
    views_count = db.Column(db.Integer, default=0)
    applications_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Clé étrangère
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # ============================================
    # RELATIONS
    # ============================================
    
    applications = db.relationship('JobApplication', backref='job', lazy='dynamic',
                                    cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Job {self.title}>'


# ============================================
# CANDIDATURE (Job Application)
# ============================================
class JobApplication(db.Model):
    __tablename__ = 'job_application'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Message de candidature
    cover_letter = db.Column(db.Text)
    
    # Liens
    resume_url = db.Column(db.String(500))
    portfolio_url = db.Column(db.String(500))
    
    # Statut
    status = db.Column(db.String(50), default='pending')
    # pending, reviewed, accepted, rejected
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    
    def __repr__(self):
        return f'<JobApplication {self.id}>'