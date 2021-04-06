from django.utils import timezone

from core import models


def get_proxy():
    proxy = models.Proxy.objects.filter(available=True).order_by("last_time_checked").first()
    if proxy is not None:
        proxy.last_time_checked = timezone.now()
        proxy.save()
    return proxy


def find_value(html, key, num_sep_chars=2, separator='"', is_first=False):
    # define the start position by the position of the key +
    # length of key + separator length (usually : and ")
    if is_first:
        start_pos = html.find(key)
    else:
        start_pos = html.rfind(key)
    if start_pos == -1:
        return None
    start_pos += len(key) + num_sep_chars

    # the end position is the position of the separator (such as ")
    # starting from the start_pos
    end_pos = html.find(separator, start_pos)
    # return the content in this range
    return html[start_pos:end_pos]
