from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from elasticsearch_dsl import connections

from apps.search.documents import GoodsSKUIndex
from .models import GoodsSKU

es = connections.get_connection()


# Signal to save each new blog post instance into ElasticSearch
@receiver(post_save, sender=GoodsSKU)
def index_post(sender, instance, **kwargs):
    instance.indexing()


# Signal to delete each new blog post instance into ElasticSearch
@receiver(post_delete, sender=GoodsSKU)
def delete_post(sender, instance, **kwargs):
    es.delete(index=GoodsSKUIndex.Index.name, doc_type="doc", id=instance.id)
