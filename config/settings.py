
import os
from pathlib import Path
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# .env ファイルを読む
env_path = BASE_DIR / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            # 空行・コメント行は無視
            if not line or line.startswith("#"):
                continue
            # = が無い行も無視
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)

# ---- 環境変数（標準） ----
SECRET_KEY = os.environ["SECRET_KEY"] 
DEBUG = os.environ.get("DEBUG", "False") == "True"

if DEBUG:
    # デバッグ環境では固定
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
else:
    # 本番環境では環境変数から取得、カンマ区切りをリストに変換
    ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

print("ALLOWED_HOSTS:", ALLOWED_HOSTS)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
print("CSRF_TRUSTED_ORIGINS:", CSRF_TRUSTED_ORIGINS)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# ---- 管理者メール ----
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]

# ---- Gmail API ----
GMAIL_SENDER = os.environ["GMAIL_SENDER"]
GMAIL_CLIENT_ID = os.environ["GMAIL_CLIENT_ID"]
GMAIL_CLIENT_SECRET = os.environ["GMAIL_CLIENT_SECRET"]
GMAIL_REFRESH_TOKEN = os.environ["GMAIL_REFRESH_TOKEN"]


# DB
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'shop',
    'tailwind',
    'theme',
    'django_browser_reload',
    "widget_tweaks",
    'cloudinary',
    'cloudinary_storage',
]

if DEBUG:
    TAILWIND_APP_NAME = 'theme'
    if os.name == "nt":
        NPM_BIN_PATH = r"C:\Program Files\nodejs\npm.cmd"
else:
    # 本番 Docker では Tailwind 無効化
    TAILWIND_APP_NAME = None
    NPM_BIN_PATH = None

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_browser_reload.middleware.BrowserReloadMiddleware',
]



#  media: Cloudinary に保存
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary 接続情報
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ["CLOUDINARY_CLOUD_NAME"],
    'API_KEY': os.environ["CLOUDINARY_API_KEY"],
    'API_SECRET': os.environ["CLOUDINARY_API_SECRET"],
}

# static: whitenoiseで収集
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "core.context_processors.company_info",
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'ja'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
