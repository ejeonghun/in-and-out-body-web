from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    딕셔너리에서 주어진 key로 값을 반환하는 커스텀 필터.
    """
    return dictionary.get(key)


@register.filter
def split(value, delimiter=','):
    """Split a string by the given delimiter and return a list."""
    return value.split(delimiter)


@register.filter
def trim(value):
    """Remove leading and trailing whitespace from a string."""
    return value.strip() if value else value


@register.filter
def multiply_and_floor(value, factor):  # 종합 점수를 표시할 때 장고 템플릿에서 사용할 필터
    try:
        return int(float(value) * float(factor)) // 10  # 마지막 자리 제거
    except (ValueError, TypeError):
        return 0


@register.filter
def round_one_decimal(value):  # 소수점 첫번째자리까지만 출력 할 필터
    try:
        return "{:.1f}".format(float(value))  # 소수점 첫 번째 자리까지 출력
    except (ValueError, TypeError):
        return "0.0"