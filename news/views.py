"""Public views for the news portal (no login required)."""

from django.shortcuts import get_object_or_404, render

from .models import Article, Category

MAX_RELATED_ARTICLES = 3


def published_articles():
    """Published articles with their author and categories preloaded."""
    return Article.published.select_related("author").prefetch_related(
        "categories"
    )


def home(request):
    """Front page: every published article, newest first."""
    context = {"articles": published_articles()}
    return render(request, "news/home.html", context)


def article_detail(request, slug):
    """Full article plus a few related articles from the same categories."""
    article = get_object_or_404(published_articles(), slug=slug)
    related_articles = (
        published_articles()
        .filter(categories__in=article.categories.all())
        .exclude(pk=article.pk)
        .distinct()[:MAX_RELATED_ARTICLES]
    )
    context = {
        "article": article,
        "related_articles": related_articles,
    }
    return render(request, "news/article_detail.html", context)


def category_detail(request, slug):
    """A category with the published articles that belong to it."""
    category = get_object_or_404(Category, slug=slug)
    context = {
        "category": category,
        "articles": published_articles().filter(categories=category),
    }
    return render(request, "news/category_detail.html", context)
