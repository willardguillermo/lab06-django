"""Tests for the news portal: models, views, templates, admin and data."""

from datetime import datetime, timedelta
from io import StringIO
import shutil
import tempfile
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import timezone

from .models import Article, Author, Category

LIMA = ZoneInfo("America/Lima")
ADMIN_MODELS = ["category", "author", "article"]

# 1x1 transparent GIF, enough for an ImageField upload.
TINY_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
    b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)

XSS_BODY = (
    "Primer párrafo normal.\n\n"
    "Ejemplo de HTML: <strong>texto en negrita</strong> "
    "<script>alert('XSS')</script>\n\n"
    "Último párrafo."
)


def make_article(author, categories=(), **fields):
    """Create an article with sensible defaults and attach categories."""
    slug = fields.pop("slug")
    defaults = {
        "title": slug.replace("-", " ").capitalize(),
        "summary": "Resumen corto.",
        "body": "Cuerpo de la noticia.",
        "published_at": timezone.now() - timedelta(days=1),
    }
    defaults.update(fields)
    article = Article.objects.create(slug=slug, author=author, **defaults)
    article.categories.set(categories)
    return article


class TempMediaMixin:
    """Store uploaded files in a temporary MEDIA_ROOT removed afterwards."""

    @classmethod
    def setUpClass(cls):
        cls._media_root = tempfile.mkdtemp(prefix="news-tests-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)


class ModelTests(TestCase):
    """String representations, absolute URLs and the published manager."""

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Tecnología", slug="tecnologia"
        )
        cls.author = Author.objects.create(name="Lucía Ramírez")
        cls.visible = make_article(
            cls.author, [cls.category], slug="visible", title="Visible"
        )
        cls.draft = make_article(
            cls.author, [cls.category], slug="borrador", is_published=False
        )
        cls.future = make_article(
            cls.author,
            [cls.category],
            slug="futura",
            published_at=timezone.now() + timedelta(days=2),
        )

    def test_str_methods(self):
        self.assertEqual(str(self.category), "Tecnología")
        self.assertEqual(str(self.author), "Lucía Ramírez")
        self.assertEqual(str(self.visible), "Visible")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.category.get_absolute_url(), "/categorias/tecnologia/"
        )
        self.assertEqual(self.visible.get_absolute_url(), "/noticias/visible/")

    def test_published_manager_hides_drafts_and_future_articles(self):
        self.assertEqual(list(Article.published.all()), [self.visible])
        self.assertEqual(Article.objects.count(), 3)

    def test_articles_are_ordered_newest_first(self):
        older = make_article(
            self.author,
            slug="antigua",
            published_at=timezone.now() - timedelta(days=10),
        )
        self.assertEqual(list(Article.published.all()), [self.visible, older])

    def test_reverse_relations(self):
        self.assertIn(self.visible, self.category.articles.all())
        self.assertIn(self.visible, self.author.articles.all())


class HomeViewTests(TestCase):
    """Front page: inheritance, include, for/empty and filters (steps 4-6)."""

    @classmethod
    def setUpTestData(cls):
        cls.tech = Category.objects.create(name="Tecnología", slug="tecnologia")
        cls.sports = Category.objects.create(name="Deportes", slug="deportes")
        cls.author = Author.objects.create(name="Diego Huamán")
        long_summary = " ".join(f"palabra{i}" for i in range(1, 61))
        cls.newest = make_article(
            cls.author,
            [cls.tech],
            slug="la-mas-reciente",
            title="La más reciente",
            summary=long_summary,
            published_at=datetime(2025, 3, 15, 10, 30, tzinfo=LIMA),
        )
        cls.older = make_article(
            cls.author,
            [cls.sports],
            slug="una-anterior",
            title="Una anterior",
            summary=long_summary,
            published_at=datetime(2025, 1, 2, 9, 0, tzinfo=LIMA),
        )
        cls.draft = make_article(
            cls.author,
            [cls.tech],
            slug="borrador",
            title="Noticia en borrador",
            is_published=False,
        )
        cls.url = reverse("news:home")

    def test_home_returns_200_with_base_and_fragment(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "news/home.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "news/_article_card.html")

    def test_home_lists_only_published_articles_newest_first(self):
        response = self.client.get(self.url)
        self.assertEqual(
            list(response.context["articles"]), [self.newest, self.older]
        )
        self.assertContains(response, "La más reciente")
        self.assertNotContains(response, "Noticia en borrador")

    def test_title_block_is_overridden(self):
        response = self.client.get(self.url)
        self.assertContains(response, "<title>Portada · El Observador</title>")

    def test_first_card_is_featured(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'class="card card--featured"', count=1)

    def test_summary_is_truncated_with_truncatewords(self):
        response = self.client.get(self.url)
        # The featured card keeps 45 words and the others 25.
        self.assertContains(response, "palabra45 …")
        self.assertContains(response, "palabra25 …")
        self.assertNotContains(response, "palabra46")

    def test_date_filter_renders_spanish_month(self):
        response = self.client.get(self.url)
        self.assertContains(response, "15 de marzo de 2025")
        self.assertContains(response, "2 de enero de 2025")

    def test_empty_message_when_there_are_no_articles(self):
        Article.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Todavía no hay noticias publicadas.")
        self.assertTemplateNotUsed(response, "news/_article_card.html")

    def test_sidebar_counts_only_published_articles(self):
        response = self.client.get(self.url)
        counts = {
            category.slug: category.article_count
            for category in response.context["sidebar_categories"]
        }
        # The draft in Tecnología is not counted.
        self.assertEqual(counts, {"deportes": 1, "tecnologia": 1})
        self.assertContains(response, "Últimas noticias")

    def test_sidebar_empty_messages(self):
        Article.objects.all().delete()
        Category.objects.all().delete()
        response = self.client.get(self.url)
        self.assertContains(response, "Aún no hay categorías.")
        self.assertContains(response, "Aún no hay noticias publicadas.")

    def test_navigation_links_use_named_urls(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'href="/categorias/tecnologia/"')
        self.assertContains(response, 'href="/noticias/la-mas-reciente/"')
        self.assertContains(response, f'href="{reverse("admin:index")}"')


class ArticleDetailViewTests(TempMediaMixin, TestCase):
    """Article page with image, author and categories (step 7)."""

    @classmethod
    def setUpTestData(cls):
        cls.tech = Category.objects.create(name="Tecnología", slug="tecnologia")
        cls.culture = Category.objects.create(name="Cultura", slug="cultura")
        cls.author = Author.objects.create(
            name="Carmen Flores",
            email="carmen@example.com",
            bio="Editora de cultura.",
        )
        cls.article = make_article(
            cls.author,
            [cls.tech, cls.culture],
            slug="museos-virtuales",
            title="Museos virtuales",
            summary="Recorridos en 3D.",
            body="Primer párrafo.\n\nSegundo párrafo.",
            published_at=datetime(2025, 3, 15, 10, 30, tzinfo=LIMA),
            featured_image=SimpleUploadedFile(
                "museos.gif", TINY_GIF, content_type="image/gif"
            ),
        )
        cls.related = make_article(
            cls.author, [cls.culture], slug="relacionada", title="Relacionada"
        )
        cls.unrelated = make_article(
            cls.author, [], slug="sin-relacion", title="Sin relación"
        )
        cls.url = reverse("news:article_detail", args=[cls.article.slug])

    def test_detail_returns_200_and_extends_base(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "news/article_detail.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(
            response, "<title>Museos virtuales · El Observador</title>"
        )

    def test_detail_shows_image_author_and_categories(self):
        response = self.client.get(self.url)
        self.assertContains(response, '<img src="/media/articles/museos')
        self.assertContains(response, 'alt="Museos virtuales"')
        self.assertContains(response, "Carmen Flores")
        self.assertContains(response, "mailto:carmen@example.com")
        self.assertContains(response, 'href="/categorias/tecnologia/"')
        self.assertContains(response, 'href="/categorias/cultura/"')

    def test_full_date_in_spanish(self):
        response = self.client.get(self.url)
        self.assertContains(response, "sábado 15 de marzo de 2025, 10:30")

    def test_body_paragraphs_use_linebreaks(self):
        response = self.client.get(self.url)
        self.assertContains(response, "<p>Primer párrafo.</p>")
        self.assertContains(response, "<p>Segundo párrafo.</p>")

    def test_sidebar_block_super_keeps_categories(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Sobre el autor")
        self.assertContains(response, "Editora de cultura.")
        # Content inherited from base.html through {{ block.super }}.
        self.assertContains(response, '<h2 class="widget__title">Categorías</h2>')
        self.assertContains(response, "Últimas noticias")

    def test_related_articles_share_a_category(self):
        response = self.client.get(self.url)
        self.assertEqual(
            list(response.context["related_articles"]), [self.related]
        )
        self.assertContains(response, "Noticias relacionadas")

    def test_unknown_slug_returns_404(self):
        url = reverse("news:article_detail", args=["no-existe"])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_draft_and_future_articles_return_404(self):
        draft = make_article(self.author, slug="oculta", is_published=False)
        future = make_article(
            self.author,
            slug="manana",
            published_at=timezone.now() + timedelta(days=1),
        )
        for article in (draft, future):
            with self.subTest(slug=article.slug):
                response = self.client.get(article.get_absolute_url())
                self.assertEqual(response.status_code, 404)

    def test_placeholder_when_there_is_no_image(self):
        response = self.client.get(self.related.get_absolute_url())
        self.assertContains(response, "placeholder--wide")


class CategoryDetailViewTests(TestCase):
    """Category listing that reuses the card fragment (step 8)."""

    @classmethod
    def setUpTestData(cls):
        cls.tech = Category.objects.create(
            name="Tecnología",
            slug="tecnologia",
            description="Software e innovación.",
        )
        cls.sports = Category.objects.create(name="Deportes", slug="deportes")
        cls.empty = Category.objects.create(name="Cultura", slug="cultura")
        cls.author = Author.objects.create(name="Lucía Ramírez")
        cls.tech_article = make_article(
            cls.author, [cls.tech], slug="ia", title="Inteligencia artificial"
        )
        cls.sports_article = make_article(
            cls.author, [cls.sports], slug="clasico", title="Clásico empatado"
        )
        make_article(
            cls.author,
            [cls.tech],
            slug="borrador",
            title="Borrador técnico",
            is_published=False,
        )

    def get(self, category):
        response = self.client.get(category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        return response

    def test_category_page_uses_base_and_fragment(self):
        response = self.get(self.tech)
        self.assertTemplateUsed(response, "news/category_detail.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "news/_article_card.html")
        self.assertContains(response, "Software e innovación.")

    def test_category_lists_only_its_published_articles(self):
        response = self.get(self.tech)
        self.assertEqual(list(response.context["articles"]), [self.tech_article])
        self.assertContains(response, 'class="card__title"', count=1)
        self.assertContains(response, '<a href="/noticias/ia/">')
        # "Clásico empatado" may appear in the sidebar, but not as a card.
        self.assertNotContains(response, 'href="/noticias/clasico/" tabindex')
        self.assertNotContains(response, "Borrador técnico")
        self.assertContains(response, "1 noticia publicada")

    def test_active_category_is_highlighted_in_sidebar(self):
        response = self.get(self.tech)
        self.assertContains(response, "category-list__link is-active", count=1)

    def test_empty_category_shows_message(self):
        response = self.get(self.empty)
        self.assertContains(
            response, "No hay noticias publicadas en esta categoría."
        )
        self.assertContains(response, "0 noticias publicadas")
        self.assertTemplateNotUsed(response, "news/_article_card.html")

    def test_unknown_category_returns_404(self):
        url = reverse("news:category_detail", args=["no-existe"])
        self.assertEqual(self.client.get(url).status_code, 404)


class UrlTests(TestCase):
    """Named routes reverse and resolve to the expected views (step 9)."""

    def test_named_urls_reverse(self):
        cases = [
            (reverse("news:home"), "/"),
            (
                reverse("news:article_detail", args=["mi-noticia"]),
                "/noticias/mi-noticia/",
            ),
            (
                reverse("news:category_detail", args=["deportes"]),
                "/categorias/deportes/",
            ),
        ]
        for url, expected in cases:
            with self.subTest(url=expected):
                self.assertEqual(url, expected)

    def test_urls_resolve_to_view_names(self):
        self.assertEqual(resolve("/").view_name, "news:home")
        self.assertEqual(
            resolve("/noticias/x/").view_name, "news:article_detail"
        )
        self.assertEqual(
            resolve("/categorias/x/").view_name, "news:category_detail"
        )


class StaticFilesTests(TestCase):
    """{% load static %} links the CSS and logo, and finders locate them."""

    def test_finders_locate_css_and_logo(self):
        for path in ("news/css/styles.css", "news/img/logo.svg"):
            with self.subTest(path=path):
                self.assertIsNotNone(finders.find(path))

    def test_base_template_links_static_files(self):
        response = self.client.get(reverse("news:home"))
        self.assertContains(
            response, 'href="/static/news/css/styles.css"'
        )
        self.assertContains(response, 'src="/static/news/img/logo.svg"')

    @override_settings(DEBUG=True)
    def test_runserver_style_static_view_serves_css(self):
        from django.contrib.staticfiles.views import serve
        from django.test import RequestFactory

        request = RequestFactory().get("/static/news/css/styles.css")
        response = serve(request, "news/css/styles.css")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/css", response["Content-Type"])


class AdminPagesTests(TestCase):
    """Changelist, add and search pages of the customized admin (step 11)."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Admin12345!",
        )
        cls.category = Category.objects.create(
            name="Deportes", slug="deportes"
        )
        cls.author = Author.objects.create(
            name="Diego Huamán", email="diego@example.com"
        )
        cls.article = make_article(
            cls.author, [cls.category], slug="clasico", title="Clásico"
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_changelist_pages_return_200(self):
        for model_name in ADMIN_MODELS:
            with self.subTest(model=model_name):
                url = reverse(f"admin:news_{model_name}_changelist")
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_add_pages_return_200(self):
        for model_name in ADMIN_MODELS:
            with self.subTest(model=model_name):
                url = reverse(f"admin:news_{model_name}_add")
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_search_finds_results(self):
        cases = [
            ("category", "Deport"),
            ("author", "Huamán"),
            ("article", "Clásico"),
            # Articles can also be searched by author name.
            ("article", "Diego"),
        ]
        for model_name, query in cases:
            with self.subTest(model=model_name, query=query):
                url = reverse(f"admin:news_{model_name}_changelist")
                response = self.client.get(url, {"q": query})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["cl"].result_count, 1)

    def test_article_filter_by_category(self):
        url = reverse("admin:news_article_changelist")
        response = self.client.get(
            url, {"categories__id__exact": self.category.pk}
        )
        self.assertEqual(
            list(response.context["cl"].result_list), [self.article]
        )

    def test_article_change_page_returns_200(self):
        url = reverse("admin:news_article_change", args=[self.article.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("admin:news_article_changelist"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])


class LoadSampleDataCommandTests(TempMediaMixin, TestCase):
    """load_sample_data creates 3 categories, 3 authors, 6 articles."""

    def run_command(self):
        out = StringIO()
        call_command("load_sample_data", stdout=out)
        return out.getvalue()

    def counts(self):
        return (
            Category.objects.count(),
            Author.objects.count(),
            Article.objects.count(),
        )

    def test_creates_expected_data(self):
        output = self.run_command()
        self.assertEqual(self.counts(), (3, 3, 6))
        self.assertEqual(Article.published.count(), 6)
        self.assertIn("6 nuevas, 6 imágenes generadas", output)
        for article in Article.objects.all():
            with self.subTest(slug=article.slug):
                self.assertTrue(article.featured_image)
                self.assertTrue(article.categories.exists())

    def test_every_category_has_articles(self):
        self.run_command()
        for category in Category.objects.all():
            with self.subTest(category=category.slug):
                self.assertGreaterEqual(category.articles.count(), 2)

    def test_running_twice_is_idempotent(self):
        self.run_command()
        output = self.run_command()
        self.assertEqual(self.counts(), (3, 3, 6))
        self.assertIn("0 nuevas, 0 imágenes generadas", output)

    def test_sample_articles_appear_on_home(self):
        self.run_command()
        response = self.client.get(reverse("news:home"))
        self.assertEqual(len(response.context["articles"]), 6)
        self.assertContains(response, "/media/articles/")


class AutoescapeTests(TestCase):
    """HTML stored in the body is shown as text, not executed (step 12)."""

    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(name="Lucía Ramírez")
        cls.article = make_article(
            cls.author,
            slug="xss",
            title="Título con <em>HTML</em>",
            body=XSS_BODY,
        )

    def setUp(self):
        self.response = self.client.get(self.article.get_absolute_url())

    def test_script_tag_is_escaped(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(
            self.response,
            "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;",
        )
        self.assertNotContains(self.response, "<script>alert('XSS')</script>")
        # The page itself contains no <script> element at all.
        self.assertNotContains(self.response, "<script")

    def test_strong_tag_is_escaped(self):
        self.assertContains(
            self.response, "&lt;strong&gt;texto en negrita&lt;/strong&gt;"
        )
        self.assertNotContains(self.response, "<strong>texto en negrita")

    def test_linebreaks_still_produces_paragraphs(self):
        self.assertContains(self.response, "<p>Primer párrafo normal.</p>")
        self.assertContains(
            self.response,
            "<p>Ejemplo de HTML: &lt;strong&gt;texto en negrita",
        )
        self.assertContains(self.response, "<p>Último párrafo.</p>")

    def test_title_is_escaped_everywhere(self):
        self.assertContains(self.response, "Título con &lt;em&gt;HTML&lt;/em&gt;")
        self.assertNotContains(self.response, "<em>HTML</em>")

    def test_summary_on_home_card_is_escaped(self):
        Article.objects.filter(pk=self.article.pk).update(
            summary="<b>resumen</b>"
        )
        response = self.client.get(reverse("news:home"))
        self.assertContains(response, "&lt;b&gt;resumen&lt;/b&gt;")
        self.assertNotContains(response, "<b>resumen</b>")
