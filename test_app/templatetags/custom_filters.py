from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Adiciona uma classe CSS a um campo de formulário.
    """
    return field.as_widget(attrs={"class": css_class})

@register.filter
def sort(value):
    return sorted(value)

@register.filter
def field_type(field):
    return field.field.widget.__class__.__name__

@register.filter
def dict_get(d, key):
    return d.get(key)

@register.filter
def filter_by_status(assignments, status_value):
    return [a for a in assignments if a.status == status_value]

@register.filter
def abs(value):
    return builtins.abs(value)