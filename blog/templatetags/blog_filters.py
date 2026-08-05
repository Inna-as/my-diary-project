import re
from django import template

register = template.Library()

BAD_WORDS = [
    'дурак', 'идиот', 'дебил', 'тупой',
]

@register.filter(name='censor')
def censor(value):
    if not value:
        return value

    text = value
    for word in BAD_WORDS:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        replacement = word[0] + '*' * (len(word) - 1)
        text = pattern.sub(replacement, text)

    return text