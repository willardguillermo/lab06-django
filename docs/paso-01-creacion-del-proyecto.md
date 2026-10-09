# Paso 1: Creación del proyecto, Pillow y la aplicación `news`

## Objetivo

Crear el proyecto Django `config` con la aplicación `news` (portal de
noticias), instalar **Pillow** para poder usar campos `ImageField` y dejar
la configuración sensible fuera del código fuente.

## Qué se hizo

1. Se creó el entorno virtual `.venv` y se instalaron las dependencias,
   registradas en `requirements.txt`:
   - `Django` 6.1 (motor de plantillas, ORM, admin).
   - `Pillow` 12.3 (necesario para `ImageField`: valida que el archivo
     subido sea realmente una imagen; también se usa para generar las
     imágenes de ejemplo del paso 11).
   - `python-decouple` (lee variables desde `.env`).
2. Se generó el proyecto con `django-admin startproject config .` y la
   aplicación con `python manage.py startapp news`.
3. Se declaró `news` en `INSTALLED_APPS`.
4. `SECRET_KEY`, `DEBUG` y `ALLOWED_HOSTS` se leen desde `.env` con
   python-decouple. Se versiona `.env.example` como plantilla, sin secretos.
5. Idioma `es` y zona horaria `America/Lima` (las fechas de las noticias se
   muestran en español, p. ej. *15 de marzo de 2025*).
6. `.gitignore` excluye `.venv/`, `.env`, `db.sqlite3`, `media/`,
   `staticfiles/`, `__pycache__/` y el `.docx` de la guía.

## Código relevante

`requirements.txt`:

```text
Django>=6.1,<6.2
Pillow>=12.3
python-decouple>=3.8
```

`config/settings.py`:

```python
from decouple import Csv, config

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

INSTALLED_APPS = [
    # ... apps de django.contrib ...
    # Local apps
    'news',
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
```

`.env.example`:

```ini
SECRET_KEY=change-me-generate-a-random-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

## Cómo probarlo

```bash
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip list | grep -Ei "django|pillow|decouple"
python manage.py check
```

## Casos de prueba

| Caso | Resultado esperado |
|------|--------------------|
| `python manage.py check` | `System check identified no issues (0 silenced).` |
| Renombrar `.env` y ejecutar `check` | Falla con `UndefinedValueError: SECRET_KEY not found` (la clave no está en el código) |
| `python -c "import PIL; print(PIL.__version__)"` | Muestra la versión de Pillow (12.3.x) |
| `git status` | No aparecen `.env`, `.venv/`, `db.sqlite3` ni `media/` |

## Resultado

Proyecto `config` con la app `news` registrada, dependencias fijadas y
secretos fuera del repositorio.

## Captura sugerida

Terminal con el entorno virtual activo, `pip list` mostrando Django, Pillow
y python-decouple, y la salida de `python manage.py check` sin errores.
