from django.apps import AppConfig


class GoodsConfig(AppConfig):
    name = 'apps.goods'

    def ready(self):
        import apps.goods.signals
