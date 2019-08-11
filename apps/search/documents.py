from itertools import chain

import boto3
from django.conf import settings
from elasticsearch import RequestsHttpConnection
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Q, Document, Text, Search, InnerDoc, Nested, analyzer, connections
from requests_aws4auth import AWS4Auth

from apps.goods import models

es_host = settings.AWS_ES_ENDPOINT
es_port = settings.AWS_ES_PORT
es_region = settings.AWS_ES_REGION
service = 'es'

credentials = boto3.Session().get_credentials()
aws_auth = AWS4Auth(credentials.access_key, credentials.secret_key, es_region, service)

es = connections.create_connection(
    hosts=[{'host': es_host, 'port': int(es_port)}],
    http_auth=aws_auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

html_strip = analyzer('html_strip',
                      tokenizer="letter",
                      filter=["lowercase", "stop", "snowball"],
                      char_filter=["html_strip"]
                      )


# ElasticSearch "model" mapping out what fields to index
class GoodsTypeIndex(InnerDoc):
    name = Text(analyzer=html_strip)


class GoodsSKUIndex(Document):
    name = Text(analyzer=html_strip)
    desc = Text(analyzer=html_strip)
    types = Nested(GoodsTypeIndex)

    class Index:
        index = 'goodssku-index'
        name = 'goodssku-index'

    def add_types(self, name):
        self.types.append(GoodsTypeIndex(name=name))

    def save(self, **kwargs):
        return super(GoodsSKUIndex, self).save(**kwargs)

    def delete(self, **kwargs):
        super(GoodsSKUIndex, self).delete(**kwargs)

    # Simple search function, return id
    def search(query="", nested_path="types"):
        q1 = Q("multi_match", query=query)
        q2 = Q('nested',
               inner_hits={},
               path=nested_path,
               query=Q('multi_match',
                       query=query))

        s1 = Search().query(q1)
        s2 = Search().query(q2)
        response1 = s1.execute()
        response2 = s2.execute()
        result1 = (hit.meta.id for hit in response1 if hit.meta)
        result2 = (hit.meta.id for hit in response2 if hit.meta)
        ids = chain(result1, result2)
        return ids


# Bulk indexing function, run in shell
def bulk_indexing():
    GoodsSKUIndex.init()
    bulk(client=es, actions=(goods_sku.indexing() for goods_sku in models.GoodsSKU.objects.all().iterator()))


# Bulk deleting function, run in shell
def bulk_deleting():
    es.indices.delete(index=GoodsSKUIndex.Index.name, ignore=[400, 404])
