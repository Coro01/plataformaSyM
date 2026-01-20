import os # Importación esencial para la configuración de MEDIA
import dj_database_url  # <--- Agrega esta línea
from pathlib import Path

# Construye rutas dentro del proyecto como esta: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_DATOS_EXTERNA = r'\\Nassmauto\Data'
# Secreto de seguridad. ¡Cámbialo en producción!
SECRET_KEY = 'tu-clave-secreta-aqui' 

# Configuración de Desarrollo
DEBUG = True
ALLOWED_HOSTS = ['plataformasym.onrender.com', '127.0.0.1', 'localhost']
# Permite que Django confíe en el dominio de Render para las galletas CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://plataformasym.onrender.com',
]

# Configuración adicional de seguridad para producción
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# --- LISTAS DE CONFIGURACIÓN ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes', 
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Aplicaciones de terceros
    'widget_tweaks',
    
    # Mis aplicaciones (PROYECTO MODULAR)
    'control_horas', 
    'compras',       # Módulo Compras
    'comercial',     # Módulo Comercial
    'rrhh',  # Módulo RRHH
    'clientes',  # Módulo Clientes
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # <--- AGREGAR ESTA LÍNEA
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mi_proyecto.urls'

# Database (SQLite3 - No requiere servidor externo)
# Configuración de Base de Datos Inteligente
DATABASES = {
    'default': dj_database_url.config(
        # Busca la variable de Render, si no existe usa SQLite para no dar error de build
        default=os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600,
        ssl_require=True # Esto fuerza el SSL que Supabase exige
    )
}
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates', 
        
        # Directorio para templates globales. ¡Es importante!
        'DIRS': [BASE_DIR / 'templates'], 
        
        # Le dice a Django que busque templates dentro de cada app
        'APP_DIRS': True, 
        
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mi_proyecto.wsgi.application'

# ... (Configuración de validación de contraseñas)

# --- LOCALIZACIÓN ---
LANGUAGE_CODE = 'es-es'

# ¡Importante! Asegúrate de que esta sea la zona horaria correcta
TIME_ZONE = 'America/Asuncion' 

USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS ---
# 3. Configurar archivos estáticos al final del archivo
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Directorios adicionales donde Django buscará archivos estáticos (opcional)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# ==========================================================
# 🛑 CONFIGURACIÓN DE ARCHIVOS DE MEDIA (CORRECCIÓN AÑADIDA) 🛑
# ==========================================================
# Ruta ABSOLUTA en el disco donde se guardarán los archivos subidos (ej: PDFs)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media') 

# URL pública que se usa para acceder a estos archivos en el navegador
MEDIA_URL = '/media/'

# --- CONFIGURACIÓN DE SESIÓN Y AUTENTICACIÓN ---

# Cierra la sesión automáticamente cuando el usuario cierra el navegador.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Tiempo de vida de la cookie de sesión (30 minutos en este caso)
SESSION_COOKIE_AGE = 60 * 30 
SESSION_SAVE_EVERY_REQUEST = True 

# URL para el login
LOGIN_URL = '/SYM/login/'

# URL a la que redirigir tras un login exitoso.
LOGIN_REDIRECT_URL = '/SYM/inicio/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'