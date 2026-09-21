import os
import sys

def list_files(startpath, exclude_dirs={'.venv', 'venv', '__pycache__'}):
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for f in files:
            print(f'{subindent}{f}')

# Пренасочваме изхода към файл
with open('структура_без_venv.txt', 'w', encoding='utf-8') as f:
    sys.stdout = f
    list_files(r'C:\MyProject\Python\MagDip')
    sys.stdout = sys.__stdout__  # връщаме обратно към конзолата

print("Готово! Файлът 'структура_без_venv.txt' е създаден.")