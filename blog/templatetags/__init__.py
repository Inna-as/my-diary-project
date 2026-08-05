import re
from django import template

register = template.Library()

# Слова для замены
BAD_WORDS = [
    'дурак', 'идиот', 'дебил', 'тупой',
    # добавь свои
]


@register.filter(name='censor')
def censor(value):
    """
    Заменяет мат-слова на ***, сохраняя регистр первой буквы.
    Пример: «Ты дурак!» → «Ты д***!»
    """
    if not value:
        return value

    text = value
    for word in BAD_WORDS:
        # Игнорируем регистр
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        replacement = word[0] + '*' * (len(word) - 1)
        text = pattern.sub(replacement, text)

    return text