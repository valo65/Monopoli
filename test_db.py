import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learing_monpoly.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        row = cursor.fetchone()
        print(f"✅ Успешно свързан с MySQL! Версия: {row[0]}")
except Exception as e:
    print(f"❌ Грешка: {e}")