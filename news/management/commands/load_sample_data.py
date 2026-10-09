"""Load sample categories, authors and articles for the news portal.

The command is idempotent: every object is matched by its slug (or email
for authors) through update_or_create, and featured images are only
generated when the article does not have one yet.
"""

from datetime import timedelta
from io import BytesIO
import textwrap
import unicodedata

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from news.models import Article, Author, Category

IMAGE_SIZE = (1200, 675)

# slug -> (name, description, RGB color used for the generated images)
CATEGORIES = {
    "tecnologia": (
        "Tecnología",
        "Novedades sobre software, inteligencia artificial, ciberseguridad "
        "y el ecosistema tecnológico peruano.",
        (37, 99, 235),
    ),
    "deportes": (
        "Deportes",
        "Resultados, análisis y crónicas del fútbol, el vóley y los "
        "deportes de aventura.",
        (22, 163, 74),
    ),
    "cultura": (
        "Cultura",
        "Música, cine, literatura, gastronomía y patrimonio cultural.",
        (219, 39, 119),
    ),
}

# email -> (name, bio)
AUTHORS = {
    "lucia.ramirez@noticias.pe": (
        "Lucía Ramírez",
        "Periodista especializada en tecnología e innovación. Cubre "
        "startups, ciberseguridad y transformación digital.",
    ),
    "diego.huaman@noticias.pe": (
        "Diego Huamán",
        "Cronista deportivo con diez años de experiencia en coberturas "
        "nacionales e internacionales.",
    ),
    "carmen.flores@noticias.pe": (
        "Carmen Flores",
        "Editora de la sección de cultura. Escribe sobre música, cine "
        "y patrimonio.",
    ),
}

# Slug of the article whose body contains raw HTML to demonstrate autoescape.
XSS_DEMO_SLUG = "como-proteger-tu-sitio-web-de-ataques-xss"

ARTICLES = [
    {
        "slug": "universidades-peruanas-apuestan-por-la-inteligencia-artificial",
        "title": "Universidades peruanas apuestan por la inteligencia artificial",
        "author": "lucia.ramirez@noticias.pe",
        "categories": ["tecnologia", "cultura"],
        "days_ago": 1,
        "summary": (
            "Varias universidades e institutos del país incorporan cursos de "
            "inteligencia artificial en sus mallas curriculares. La meta es "
            "formar profesionales capaces de aplicar estas herramientas en la "
            "industria local."
        ),
        "body": (
            "Durante el último año, al menos una decena de casas de estudio "
            "anunciaron nuevos cursos y diplomados enfocados en aprendizaje "
            "automático, procesamiento de lenguaje natural y visión por "
            "computadora.\n\n"
            "Los coordinadores académicos coinciden en que la demanda de "
            "perfiles especializados crece más rápido que la oferta. Por ello, "
            "los programas combinan fundamentos matemáticos con proyectos "
            "aplicados a problemas reales de empresas peruanas.\n\n"
            "Los estudiantes, por su parte, valoran la posibilidad de trabajar "
            "con datos abiertos del Estado y de participar en competencias "
            "internacionales. Varios equipos ya obtuvieron premios en "
            "hackatones regionales.\n\n"
            "Los especialistas advierten, sin embargo, que la formación ética "
            "debe acompañar a la técnica para evitar sesgos y usos indebidos "
            "de estas tecnologías."
        ),
    },
    {
        "slug": XSS_DEMO_SLUG,
        "title": "Cómo proteger tu sitio web de ataques XSS",
        "author": "lucia.ramirez@noticias.pe",
        "categories": ["tecnologia"],
        "days_ago": 5,
        "summary": (
            "El cross-site scripting sigue siendo una de las vulnerabilidades "
            "web más comunes. Los frameworks modernos ofrecen defensas por "
            "defecto, pero conviene entender cómo funcionan."
        ),
        "body": (
            "Un ataque XSS ocurre cuando una aplicación muestra contenido "
            "enviado por un usuario sin escaparlo, permitiendo que el "
            "navegador ejecute código JavaScript malicioso.\n\n"
            "Motores de plantillas como el de Django aplican autoescape: "
            "convierten caracteres como < y > en entidades HTML antes de "
            "mostrarlos. Observa cómo se muestra la siguiente línea:\n\n"
            "Ejemplo de HTML: <strong>texto en negrita</strong> "
            "<script>alert('XSS')</script>\n\n"
            "Si el autoescape está activo, verás las etiquetas como texto "
            "literal y no aparecerá ninguna alerta. Solo se debe usar el "
            "filtro safe o mark_safe con contenido de confianza.\n\n"
            "Además del escape, se recomienda validar las entradas, usar "
            "cabeceras Content-Security-Policy y mantener actualizadas las "
            "dependencias del proyecto."
        ),
    },
    {
        "slug": "alianza-y-universitario-empatan-en-un-clasico-intenso",
        "title": "Alianza y Universitario empatan en un clásico intenso",
        "author": "diego.huaman@noticias.pe",
        "categories": ["deportes"],
        "days_ago": 3,
        "summary": (
            "El clásico del fútbol peruano terminó igualado 1 a 1 ante un "
            "estadio lleno. Ambos equipos mantienen sus opciones en la pelea "
            "por el torneo."
        ),
        "body": (
            "El primer tiempo fue de dominio local, con llegadas constantes "
            "por las bandas y un gol de cabeza tras un tiro de esquina a los "
            "veinte minutos.\n\n"
            "En la segunda mitad, la visita adelantó sus líneas y encontró el "
            "empate mediante un remate de media distancia que se coló junto "
            "al poste.\n\n"
            "Los entrenadores destacaron la entrega de sus jugadores y "
            "coincidieron en que el resultado fue justo por lo mostrado en "
            "el campo.\n\n"
            "Con este empate, la tabla de posiciones se mantiene ajustada a "
            "falta de cinco fechas para el cierre del campeonato."
        ),
    },
    {
        "slug": "seleccion-femenina-de-voley-clasifica-al-mundial",
        "title": "Selección femenina de vóley clasifica al Mundial",
        "author": "diego.huaman@noticias.pe",
        "categories": ["deportes", "cultura"],
        "days_ago": 9,
        "summary": (
            "El equipo nacional aseguró su lugar en el Mundial tras vencer en "
            "cinco sets a su rival directo. La hinchada celebró en las calles "
            "un logro esperado durante años."
        ),
        "body": (
            "El partido fue un ir y venir de emociones: las peruanas perdían "
            "dos sets a uno, pero reaccionaron con un bloqueo sólido y un "
            "saque agresivo.\n\n"
            "La capitana fue la máxima anotadora del encuentro y dedicó el "
            "triunfo a las generaciones que forjaron la tradición del vóley "
            "nacional.\n\n"
            "El comando técnico anunció que el grupo seguirá concentrado para "
            "una gira de preparación por Europa y Asia antes del torneo.\n\n"
            "Más allá del resultado, la clasificación reaviva el interés de "
            "niñas y jóvenes por este deporte, que forma parte de la "
            "identidad cultural del país."
        ),
    },
    {
        "slug": "festival-de-cine-de-lima-presenta-su-programacion",
        "title": "Festival de Cine de Lima presenta su programación",
        "author": "carmen.flores@noticias.pe",
        "categories": ["cultura"],
        "days_ago": 14,
        "summary": (
            "La nueva edición del festival reunirá más de cien películas de "
            "Iberoamérica. Habrá funciones gratuitas en parques y centros "
            "culturales de varios distritos."
        ),
        "body": (
            "La organización presentó una selección que incluye largometrajes "
            "de ficción, documentales y cortometrajes realizados por nuevos "
            "directores de la región.\n\n"
            "Entre las novedades destaca una sección dedicada al cine "
            "amazónico y una retrospectiva de clásicos del cine peruano "
            "restaurados digitalmente.\n\n"
            "Las funciones al aire libre buscan acercar el séptimo arte a "
            "públicos que normalmente no acceden a las salas comerciales.\n\n"
            "Las entradas para las salas principales estarán disponibles en "
            "línea desde la próxima semana."
        ),
    },
    {
        "slug": "museos-digitalizan-su-patrimonio-con-realidad-virtual",
        "title": "Museos digitalizan su patrimonio con realidad virtual",
        "author": "carmen.flores@noticias.pe",
        "categories": ["cultura", "tecnologia"],
        "days_ago": 21,
        "summary": (
            "Museos de Lima y Cusco lanzan recorridos virtuales de sus "
            "colecciones. La iniciativa permite visitar piezas arqueológicas "
            "desde cualquier lugar del mundo."
        ),
        "body": (
            "El proyecto utilizó fotogrametría y escaneo 3D para registrar "
            "cerámicas, textiles y orfebrería con un alto nivel de detalle.\n\n"
            "Los visitantes pueden recorrer las salas con un visor de "
            "realidad virtual o directamente desde el navegador de su "
            "computadora o celular.\n\n"
            "Los curadores señalan que la digitalización también ayuda a la "
            "conservación, pues reduce la manipulación de piezas frágiles.\n\n"
            "La segunda etapa incorporará guías narradas en quechua, aimara "
            "y castellano para ampliar el alcance educativo de la iniciativa."
        ),
    },
]


def _load_font(size):
    """Return a scalable default font, falling back to the bitmap one."""
    try:
        return ImageFont.load_default(size=size)
    except (TypeError, OSError):
        return ImageFont.load_default()


def _ascii(text):
    """Strip accents: Pillow's built-in font only covers basic ASCII."""
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def build_featured_image(title, category_name, color):
    """Create a gradient JPEG with the category label and the title."""
    width, height = IMAGE_SIZE
    image = Image.new("RGB", IMAGE_SIZE)
    draw = ImageDraw.Draw(image)

    # Vertical gradient from the category color to a darker shade.
    dark = tuple(int(channel * 0.35) for channel in color)
    for y in range(height):
        ratio = y / (height - 1)
        row_color = tuple(
            int(color[i] + (dark[i] - color[i]) * ratio) for i in range(3)
        )
        draw.line([(0, y), (width, y)], fill=row_color)

    draw.text(
        (80, 80), _ascii(category_name).upper(), font=_load_font(40), fill="white"
    )
    title_font = _load_font(64)
    y = 220
    for line in textwrap.wrap(_ascii(title), width=30):
        draw.text((80, y), line, font=title_font, fill="white")
        y += 84

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = (
        "Carga datos de ejemplo: 3 categorías, 3 autores y 6 noticias "
        "publicadas con imágenes generadas. Es idempotente. La noticia "
        f"'{XSS_DEMO_SLUG}' incluye HTML (<strong> y <script>) en su cuerpo "
        "para demostrar el autoescape de las plantillas."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for slug, (name, description, _color) in CATEGORIES.items():
            categories[slug], _ = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "description": description},
            )

        authors = {}
        for email, (name, bio) in AUTHORS.items():
            authors[email], _ = Author.objects.update_or_create(
                email=email, defaults={"name": name, "bio": bio}
            )

        now = timezone.now()
        created_count = 0
        image_count = 0
        for data in ARTICLES:
            article, created = Article.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "title": data["title"],
                    "summary": data["summary"],
                    "body": data["body"],
                    "author": authors[data["author"]],
                    "published_at": now - timedelta(days=data["days_ago"]),
                    "is_published": True,
                },
            )
            created_count += created
            article.categories.set(
                [categories[slug] for slug in data["categories"]]
            )

            # Only generate an image once, so reruns don't duplicate files.
            if not article.featured_image:
                main_slug = data["categories"][0]
                name, _description, color = CATEGORIES[main_slug]
                article.featured_image.save(
                    f"{article.slug}.jpg",
                    build_featured_image(article.title, name, color),
                    save=True,
                )
                image_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Datos de ejemplo cargados: "
                f"{Category.objects.count()} categorías, "
                f"{Author.objects.count()} autores, "
                f"{Article.objects.count()} noticias "
                f"({created_count} nuevas, {image_count} imágenes generadas)."
            )
        )
        self.stdout.write(
            "Demo de autoescape (paso 12): la noticia "
            f"'{XSS_DEMO_SLUG}' contiene <strong> y <script> en su cuerpo."
        )
