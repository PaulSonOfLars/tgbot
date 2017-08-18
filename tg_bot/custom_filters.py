from telegram.ext import BaseFilter


class __SimaoFilter(BaseFilter):
    def filter(self, message):
        return 'simao' in message.text.lower()


SimaoFilter = __SimaoFilter()
