from retry import retry
import tweepy

from rainman import cache, paginated_cache
from tweepy import TooManyRequests

from community.app import settings

AUTH = tweepy.OAuthHandler(settings.TWITTER_API_KEY, settings.TWITTER_SECRET_KEY)
AUTH.set_access_token(settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_TOKEN_SECRET)
API = tweepy.API(AUTH)
CLIENT = tweepy.Client(consumer_key=settings.TWITTER_API_KEY,
                       consumer_secret=settings.TWITTER_SECRET_KEY,
                       access_token=settings.TWITTER_ACCESS_TOKEN,
                       access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
                       bearer_token=settings.TWITTER_BEARER_TOKEN)
MEDIA_FIELDS = [
    'duration_ms',
    'height',
    'media_key',
    'preview_image_url',
    'type',
    'url',
    'width',
    'public_metrics',
    'non_public_metrics',
    'organic_metrics',
    'promoted_metrics'
]
PLACE_FIELDS = [
    'contained_within',
    'country',
    'country_code',
    'full_name',
    'geo',
    'id',
    'name',
    'place_type'
]
TWEET_FIELDS = [
    'attachments',
    'author_id',
    'context_annotations',
    'conversation_id',
    'created_at',
    'entities',
    'geo',
    'id',
    'in_reply_to_user_id',
    'lang',
    'non_public_metrics',
    'public_metrics',
    'organic_metrics',
    'promoted_metrics',
    'possibly_sensitive',
    'referenced_tweets',
    'reply_settings',
    'source',
    'text',
    'withheld'
]
USER_FIELDS = [
    'created_at',
    'description',
    'entities',
    'id',
    'location',
    'name',
    'pinned_tweet_id',
    'profile_image_url',
    'protected',
    'public_metrics',
    'url',
    'username',
    'verified',
    'withheld'
]


@staticmethod
def to_users(data_set):
    return [tweepy.User(data) for data in data_set]


@staticmethod
def to_tweets(data_set):
    return [tweepy.Tweet(data) for data in data_set]


@paginated_cache(to_python=to_tweets)
def get_tweets(query, pagination_token=None):
    resp = CLIENT.get_users_tweets(query, max_results=100, pagination_token=pagination_token)
    next_token = resp.meta.get('next_token')
    value = [obj.data for obj in resp.data]
    return value, next_token


@paginated_cache(to_python=to_tweets)
def get_user_mentions(user_id, pagination_token=None):
    resp = CLIENT.get_users_mentions(user_id, max_results=100, pagination_token=pagination_token)
    next_token = resp.meta.get('next_token')
    value = [obj.data for obj in resp.data]
    return value, next_token


@paginated_cache(to_python=to_users)
def get_user_followers(user_id, pagination_token=None):
    resp = CLIENT.get_users_followers(user_id,
                                      max_results=1000,
                                      pagination_token=pagination_token,
                                      user_fields=USER_FIELDS)
    next_token = resp.meta.get('next_token')
    value = [obj.data for obj in resp.data]
    return value, next_token


@cache(to_python=to_users)
def get_users(id_set):
    resp = CLIENT.get_users(ids=id_set, user_fields=USER_FIELDS)
    value = [obj.data for obj in resp.data]
    return value


@cache(to_python=to_users)
@retry(TooManyRequests, tries=1000, delay=30)
def get_liking_users(tweet_id):
    from tweepy import User

    route = '/2/tweets/%s/liking_users' % tweet_id
    resp = CLIENT._make_request(
        method="GET",
        route=route,
        endpoint_parameters=(
            "ids", "usernames", "expansions", "tweet.fields", "user.fields"
        ),
        data_type=User,
        params={
            # 'media.fields': ','.join(MEDIA_FIELDS),
            # 'place.fields': ','.join(PLACE_FIELDS),
            # 'tweet.fields': ','.join(TWEET_FIELDS),
            'user.fields': ','.join(USER_FIELDS)
        }
    )
    return [obj.data for obj in resp.data or []]


@staticmethod
def to_users_v1(data_set):
    return [tweepy.models.User(data) for data in data_set]


@paginated_cache(to_python=to_users_v1)
def get_user_friends(user_id, cursor=-1):
    resp, cursors = API.get_friends(user_id=user_id, count=200, cursor=cursor)
    next_cursor = cursors[-1]
    if next_cursor == 0:
        next_cursor = None
    value = [obj._json for obj in resp]
    return value, next_cursor


def object_to_dict(obj, *skip_keys):
    return {k: getattr(obj, k) for k in dir(obj) if not k.startswith('_') and k not in skip_keys}


def skip_keys(d, *keys):
    return {k: v for k, v in d.items() if k not in keys}
