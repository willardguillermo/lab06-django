# Paso 12: Prueba del escapado automático (autoescape)

## Objetivo

Guardar etiquetas HTML en el cuerpo de una noticia, observar qué muestra la
página y explicar por qué el motor de plantillas de Django protege contra
ataques **XSS** (*cross-site scripting*).

## Qué se hizo

1. La noticia **"Cómo proteger tu sitio web de ataques XSS"**
   (slug `como-proteger-tu-sitio-web-de-ataques-xss`, creada por
   `load_sample_data`) tiene en su cuerpo esta línea, guardada tal cual en
   la base de datos:

   ```html
   Ejemplo de HTML: <strong>texto en negrita</strong> <script>alert('XSS')</script>
   ```

   Lo mismo puede hacerse a mano desde el admin, editando el campo
   *Cuerpo* de cualquier noticia.
2. La plantilla `news/article_detail.html` muestra el cuerpo con
   `{{ article.body|linebreaks }}`, **sin** `|safe` y sin desactivar el
   autoescape.
3. Se agregaron pruebas automáticas (`AutoescapeTests`) y se revisó el HTML
   real que entrega el servidor de desarrollo.

## Qué muestra la página

En el navegador, el párrafo se ve **como texto literal**:

> Ejemplo de HTML: &lt;strong&gt;texto en negrita&lt;/strong&gt; &lt;script&gt;alert('XSS')&lt;/script&gt;

- `texto en negrita` **no** aparece en negrita: se ven las etiquetas
  `<strong>` y `</strong>` escritas.
- El `<script>` **no se ejecuta**: no aparece ninguna ventana de alerta.
  Se ve el código como texto.

HTML real recibido por el navegador (obtenido con `django.test.Client`
sobre la base de datos de desarrollo, GET
`/noticias/como-proteger-tu-sitio-web-de-ataques-xss/`):

```html
<p>Ejemplo de HTML: &lt;strong&gt;texto en negrita&lt;/strong&gt; &lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;</p>
```

En toda la página no hay ni un solo `<script` (la búsqueda devuelve 0
coincidencias): el código del usuario nunca llega a ser una etiqueta.

## Por qué ocurre

Django aplica **escapado automático** a toda expresión `{{ variable }}`:
antes de insertar el valor en el HTML reemplaza los caracteres especiales
por **entidades HTML**:

| Carácter | Entidad |
|----------|---------|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `'` | `&#x27;` |
| `"` | `&quot;` |
| `&` | `&amp;` |

El navegador dibuja una entidad como el carácter correspondiente, pero ya
no la interpreta como el inicio de una etiqueta. Por eso `<script>` se ve
en pantalla pero no se ejecuta.

**¿Y `|linebreaks`?** El filtro primero **escapa** el texto (porque el
autoescape está activo) y **después** agrega sus propias etiquetas `<p>` y
`<br>` según los saltos de línea, marcando el resultado como seguro. Por eso
el cuerpo conserva sus párrafos (`<p>...</p>` reales, creados por Django)
mientras que las etiquetas escritas por el usuario quedan escapadas.

Lo mismo aplica al título, al resumen, al nombre del autor, etc.: cualquier
`{{ }}` del portal está protegido (hay pruebas para el título y para el
resumen en la portada).

## Qué pasaría si se desactiva el escapado (y por qué es peligroso)

Con `{{ article.body|safe|linebreaks }}` o con
`{% autoescape off %}{{ article.body|linebreaks }}{% endautoescape %}`
Django insertaría el texto sin cambios:

```html
<p>Ejemplo de HTML: <strong>texto en negrita</strong> <script>alert('XSS')</script></p>
```

- `texto en negrita` se vería en negrita.
- El navegador **ejecutaría** el `<script>` y mostraría la alerta.

Una alerta es inofensiva, pero el mismo hueco permite que quien escriba en
el campo ejecute **cualquier** JavaScript en el navegador de cada lector
(o de un administrador que abra la página): robar cookies o tokens de
sesión, hacer peticiones en su nombre, modificar la página para pedir
contraseñas (*phishing*) o redirigir a sitios maliciosos. Eso es un ataque
**XSS almacenado**. `|safe`, `mark_safe()` y `{% autoescape off %}` solo
deben usarse con contenido 100 % de confianza, nunca con texto escrito por
usuarios.

## Alternativas seguras si se necesita formato

1. **Texto plano + filtros** (lo que hace este proyecto): `linebreaks`
   convierte saltos de línea en párrafos sin aceptar HTML del usuario.
2. **`format_html()`** en Python cuando se arma HTML con datos variables:
   escapa cada argumento y solo confía en la plantilla fija (el admin lo
   usa para la miniatura de la noticia).
3. **Sanitizar con una lista blanca** (por ejemplo con la biblioteca
   *bleach* o *nh3*): permitir solo etiquetas inocuas (`<strong>`, `<em>`,
   `<a href>`…) y eliminar `<script>`, atributos `on*`, `javascript:` en
   enlaces, etc.; solo el resultado sanitizado se marca como seguro.
4. **Markdown**: el autor escribe `**negrita**`, se convierte a HTML y
   luego se sanitiza con la lista blanca antes de mostrarlo.
5. Defensa adicional: cabecera **Content-Security-Policy** que impida
   ejecutar scripts en línea.

## Código relevante

`templates/news/article_detail.html`:

```django
{# Autoescaping stays on: any HTML in the body is shown as text. #}
<div class="article__body">
  {{ article.body|linebreaks }}
</div>
```

`news/tests.py` (fragmento):

```python
def test_script_tag_is_escaped(self):
    self.assertContains(
        self.response,
        "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;",
    )
    self.assertNotContains(self.response, "<script>alert('XSS')</script>")
    # The page itself contains no <script> element at all.
    self.assertNotContains(self.response, "<script")
```

## Cómo probarlo

```bash
python manage.py load_sample_data
python manage.py runserver
# Abrir http://127.0.0.1:8000/noticias/como-proteger-tu-sitio-web-de-ataques-xss/
# Clic derecho → "Ver código fuente" y buscar "&lt;script"

python manage.py test news.tests.AutoescapeTests -v 2
```

## Casos de prueba

| Prueba | Resultado esperado |
|--------|--------------------|
| `test_script_tag_is_escaped` | Aparece `&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;`; no hay ningún `<script` en la página |
| `test_strong_tag_is_escaped` | Aparece `&lt;strong&gt;texto en negrita&lt;/strong&gt;`, no la etiqueta real |
| `test_linebreaks_still_produces_paragraphs` | Los párrafos siguen envueltos en `<p>` reales |
| `test_title_is_escaped_everywhere` | Un `<em>` en el título se muestra como `&lt;em&gt;` (en `<title>`, `<h1>` y migas) |
| `test_summary_on_home_card_is_escaped` | Un `<b>` en el resumen se escapa en la tarjeta de la portada |
| Manual en el navegador | Se ven las etiquetas como texto y **no** aparece ninguna alerta |

## Resultado

El autoescape de Django está activo por defecto y convierte el HTML
guardado por un usuario en texto inofensivo; el portal es seguro frente a
XSS almacenado mientras no se use `|safe` con contenido no confiable.

## Captura sugerida

1. La noticia en el navegador mostrando las etiquetas como texto (sin
   alerta).
2. *Ver código fuente* con la línea `&lt;script&gt;...` resaltada.
3. El campo *Cuerpo* en el admin con el HTML original guardado.
