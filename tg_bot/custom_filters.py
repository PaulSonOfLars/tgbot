from telegram.ext import BaseFilter


class __SimaoFilter(BaseFilter):
    def filter(self, message):
        return 'simao' in message.text.lower()


SimaoFilter = __SimaoFilter()


class __HashFilter(BaseFilter):
    def filter(self, message):
        # NOTE: assumes message is parsed in order, and hashtag is always first
        return message.entities and any(msg.type == 'hashtag' for msg in message.entities)

HashFilter = __HashFilter()
