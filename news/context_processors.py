"""Context processors that feed the shared portal layout (base.html)."""

from django.db.models import Count, Q
from django.utils import timezone

from .models import Article, Category

LATEST_ARTICLES_LIMIT = 5


def portal_sidebar(request):
    """Add the categories and latest articles shown in the sidebar.

    Querysets are lazy, so pages that override the sidebar block without
    using these variables do not hit the database.
    """
    published = Q(
        articles__is_published=True,
        articles__published_at__lte=timezone.now(),
    )
    return {
        "sidebar_categories": Category.objects.annotate(
            article_count=Count("articles", filter=published)
        ),
        "sidebar_latest_articles": Article.published.only(
            "title", "slug", "published_at"
        )[:LATEST_ARTICLES_LIMIT],
    }
