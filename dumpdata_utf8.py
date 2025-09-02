import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  
django.setup()

from django.core.management import call_command

with open('db_seed.json', 'w', encoding='utf-8') as f:
    call_command(
        'dumpdata',
        '--natural-primary',
        '--natural-foreign',
        exclude=['contenttypes', 'auth.Permission', 'sessions'],
        stdout=f
    )

print("db_seed.json を UTF-8 で出力しました。")
