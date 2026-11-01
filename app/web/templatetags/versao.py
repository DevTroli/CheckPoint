import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(caminho):
    """URL do arquivo estático com ?v=<data de modificação>.

    Quando o arquivo muda, a URL muda, e o navegador baixa a versão nova em vez de
    reaproveitar uma antiga do cache.
    """
    url = static(caminho)
    arquivo = finders.find(caminho)
    if arquivo:
        url += "?v=" + str(int(os.path.getmtime(arquivo)))
    return url
