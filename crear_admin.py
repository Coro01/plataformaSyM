import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username='Victor').exists():
    User.objects.create_superuser('Victor', '', '4545')
    print("Superusuario creado con éxito")
else:
    print("El usuario ya existe")