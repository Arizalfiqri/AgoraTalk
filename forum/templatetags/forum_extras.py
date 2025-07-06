
from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """
    Split a string by delimiter and return a list
    Usage: {{ "tag1,tag2,tag3"|split:"," }}
    """
    if not value:
        return []
    return [item.strip() for item in str(value).split(delimiter) if item.strip()]

@register.filter
def get_tags_list(value):
    """
    Convert comma-separated tags string to list
    Usage: {{ thread.tags|get_tags_list }}
    """
    if not value:
        return []
    return [tag.strip() for tag in str(value).split(',') if tag.strip()]

@register.simple_tag
def url_with_params(request, **kwargs):
    """
    Build URL with additional parameters while preserving existing ones
    Usage: {% url_with_params request page=2 sort='popular' %}
    """
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value:
            params[key] = value
        elif key in params:
            del params[key]
    
    if params:
        return f"?{params.urlencode()}"
    return ""

@register.filter
def subtract(value, arg):
    """
    Subtract arg from value
    Usage: {{ value|subtract:5 }}
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_class(field, css_class):
    """
    Add CSS class to form field
    Usage: {{ form.field|add_class:"form-control" }}
    """
    return field.as_widget(attrs={"class": css_class})

@register.filter
def highlight_search(text, search_term):
    """
    Highlight search terms in text
    Usage: {{ text|highlight_search:query }}
    """
    if not search_term or not text:
        return text
    
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    highlighted = pattern.sub(
        f'<mark class="bg-warning">{search_term}</mark>', 
        str(text)
    )
    return mark_safe(highlighted)

@register.inclusion_tag('forum/includes/pagination.html')
def render_pagination(page_obj, request):
    """
    Render pagination with current request parameters
    Usage: {% render_pagination threads request %}
    """
    return {
        'page_obj': page_obj,
        'request': request,
    }