# Paso 5: Fragmento `_article_card.html` reutilizable

## Objetivo

Escribir la tarjeta de una noticia **una sola vez** e incluirla desde la
portada y desde el listado por categoría, en lugar de duplicar el HTML.

## Qué se hizo

1. Se creó `templates/news/_article_card.html`. No extiende ninguna
   plantilla: es un fragmento que espera la variable `article` y,
   opcionalmente, `featured`.
2. La tarjeta muestra: imagen destacada (o un recuadro con la inicial del
   título si no hay imagen), etiquetas de categorías con enlace, título con
   enlace al detalle, resumen recortado, autor y fecha.
3. Se incluye con `{% include "news/_article_card.html" with article=article %}`.
   En la portada se pasa además `featured=forloop.first` para que la primera
   noticia ocupe todo el ancho y muestre un resumen más largo.
4. El comentario `{# ... #}` del inicio documenta qué variables espera.

## Código relevante

`templates/news/_article_card.html`:

```django
{# Reusable card for one article. Expects: article; optional: featured. #}
<article class="card{% if featured %} card--featured{% endif %}">
  <a class="card__media" href="{% url 'news:article_detail' article.slug %}" tabindex="-1" aria-hidden="true">
    {% if article.featured_image %}
      <img src="{{ article.featured_image.url }}" alt="" loading="lazy">
    {% else %}
      <div class="placeholder"><span class="placeholder__initial">{{ article.title|first|upper }}</span></div>
    {% endif %}
  </a>
  <div class="card__body">
    <ul class="tags" aria-label="Categorías">
      {% for category in article.categories.all %}
        <li><a class="tag" href="{% url 'news:category_detail' category.slug %}">{{ category.name }}</a></li>
      {% endfor %}
    </ul>
    <h2 class="card__title">
      <a href="{% url 'news:article_detail' article.slug %}">{{ article.title }}</a>
    </h2>
    <p class="card__summary">{% if featured %}{{ article.summary|truncatewords:45 }}{% else %}{{ article.summary|truncatewords:25 }}{% endif %}</p>
    <p class="meta">
      Por <strong>{{ article.author.name }}</strong> ·
      <time datetime="{{ article.published_at|date:'c' }}">{{ article.published_at|date:"j \d\e F \d\e Y" }}</time>
    </p>
  </div>
</article>
```

Uso desde `home.html` y `category_detail.html`:

```django
{% include "news/_article_card.html" with article=article featured=forloop.first %}
{% include "news/_article_card.html" with article=article %}
```

## Cómo probarlo

```bash
python manage.py test news.tests.HomeViewTests news.tests.CategoryDetailViewTests -v 2
```

## Casos de prueba

| Prueba | Resultado esperado |
|--------|--------------------|
| `HomeViewTests.test_home_returns_200_with_base_and_fragment` | La portada usa `news/_article_card.html` |
| `CategoryDetailViewTests.test_category_page_uses_base_and_fragment` | El listado por categoría usa el mismo fragmento |
| `HomeViewTests.test_first_card_is_featured` | Exactamente una tarjeta con `card--featured` |
| `HomeViewTests.test_empty_message_when_there_are_no_articles` | Sin noticias, el fragmento no se usa |

## Resultado

Un único archivo define cómo se ve una noticia en los listados; cambiarlo
actualiza la portada y las páginas de categoría a la vez.
