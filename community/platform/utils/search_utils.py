from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch_dsl import Search, connections
from requests_aws4auth import AWS4Auth

from community.app import settings

CONN_INITED = False


def get_connection():
    global CONN_INITED

    if not CONN_INITED:
        awsauth = AWS4Auth(settings.AWS_ACCESS_KEY, settings.AWS_SECRET_KEY, settings.AWS_REGION, 'es')
        es = Elasticsearch(
            hosts=[{'host': settings.ELASTICSEARCH_HOST, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        connections.add_connection('default', es)
        CONN_INITED = True
    return connections.get_connection()


def get_search(index):
    client = get_connection()
    return Search(using=client, index=index)


def serialize_search_results(results):
    for result in results:
        yield result._d_


def filter_values(s, field_name, values):
    from elasticsearch_dsl import Q
    q_set = [Q('match', **{field_name: v}) for v in values]
    s = s.query('bool', should=q_set)
    return s
