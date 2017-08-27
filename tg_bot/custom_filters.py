from telegram.ext import BaseFilter


class CustomFilters(object):
    class _SimaoFilter(BaseFilter):
        def filter(self, message):
            return 'simao' in message.text.lower()

    SimaoFilter = _SimaoFilter()
