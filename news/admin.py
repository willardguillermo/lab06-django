"""Admin site configuration for the news app.

Each model is registered with a customized ModelAdmin class.
"""

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Article, Author, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Categories with the number of articles that belong to each one."""

    list_display = ("name", "slug", "article_count")
    list_filter = ("articles__is_published",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(article_total=Count("articles", distinct=True))

    @admin.display(description="noticias", ordering="article_total")
    def article_count(self, obj):
        return obj.article_total


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Authors with the number of articles they have written."""

    list_display = ("name", "email", "article_count")
    list_filter = ("articles__categories",)
    search_fields = ("name", "email", "bio")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(article_total=Count("articles", distinct=True))

    @admin.display(description="noticias", ordering="article_total")
    def article_count(self, obj):
        return obj.article_total


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Articles with author, categories, publication data and thumbnail."""

    list_display = (
        "thumbnail",
        "title",
        "author",
        "category_list",
        "published_at",
        "is_published",
    )
    list_display_links = ("thumbnail", "title")
    list_editable = ("is_published",)
    list_filter = ("is_published", "categories", "author", "published_at")
    search_fields = ("title", "summary", "body", "author__name")
    prepopulated_fields = {"slug": ("title",)}
    list_select_related = ("author",)
    filter_horizontal = ("categories",)
    date_hierarchy = "published_at"
    list_per_page = 20
    readonly_fields = ("thumbnail", "created_at", "updated_at")
    fieldsets = (
        (
            "Contenido",
            {"fields": ("title", "slug", "summary", "body")},
        ),
        (
            "Imagen destacada",
            {"fields": ("featured_image", "thumbnail")},
        ),
        (
            "Autoría y clasificación",
            {"fields": ("author", "categories")},
        ),
        (
            "Publicación",
            {"fields": ("is_published", "published_at")},
        ),
        (
            "Auditoría",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("categories")

    @admin.display(description="categorías")
    def category_list(self, obj):
        # Uses the prefetched categories, so no extra query per row.
        return ", ".join(category.name for category in obj.categories.all())

    @admin.display(description="imagen")
    def thumbnail(self, obj):
        if not obj.featured_image:
            return "-"
        # format_html escapes the URL and the alt text.
        return format_html(
            '<img src="{}" alt="{}" style="height:45px;width:80px;'
            'object-fit:cover;border-radius:4px;">',
            obj.featured_image.url,
            obj.title,
        )
