import datetime
import itertools
import logging

from sqlalchemy import Column, String, Text, func, BigInteger
from sqlalchemy.sql import functions
from sqlalchemy_utils import ChoiceType
from tqdm import tqdm

from community.ingest.base.models import BaseJob, BaseSource, BaseUser, BaseMessage, \
    BaseRelation, BaseMessageReaction, BaseMessageThread

_LOG = logging.getLogger(__name__)


class TwitterHandle(BaseSource):
    REPR_FIELD = 'handle'

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    handle = Column(Text, nullable=False)

    def crawl_messages(self):
        session = self.session_factory()
        try:
            since = session.query(Tweet)\
                           .join(TwitterJob, TwitterJob.id == Tweet.job_id) \
                           .filter(TwitterJob.query == self.handle,
                                   TwitterJob.crawl_type == TwitterJob.CRAWL_TYPE_HANDLE_MESSAGES) \
                           .with_entities(functions.max(Tweet.timestamp)).one()[0]
        except IndexError:
            config = {}
        else:
            config = {'since': since}
        TwitterJob.add_job(project_id=self.project_id,
                           query=self.handle,
                           crawl_type=TwitterJob.CRAWL_TYPE_HANDLE_MESSAGES,
                           config=config)


class TwitterJob(BaseJob):
    CRAWL_TYPE_HANDLE_MESSAGES = 'handle_messages'
    CRAWL_TYPE_HASHTAG = 'hashtag'
    CRAWL_TYPES = (
        (CRAWL_TYPE_HANDLE_MESSAGES, CRAWL_TYPE_HANDLE_MESSAGES.title()),
        (CRAWL_TYPE_HASHTAG, CRAWL_TYPE_HASHTAG.title()),
    )
    BULK_CREATE_CHUNK_SIZE = 100

    query = Column(Text, nullable=False)
    crawl_type = Column(ChoiceType(CRAWL_TYPES, impl=String(25)), nullable=False)

    def __repr__(self):
        return '<%s:%s:%s:%s - %s>' % (self.__class__.__name__, self.project.name, self.query, self.config, self.status)

    @classmethod
    def add_job(cls, project_id, **kwargs):
        config = kwargs.get('config', {})
        if config.get('since'):
            config['since'] = config['since'].strftime('%Y-%m-%d')
        if config.get('until'):
            config['until'] = config['until'].strftime('%Y-%m-%d')
        super(cls, cls).add_job(project_id=project_id, **kwargs)

    @property
    def cleaned_config(self):
        defaults = {
            'since': None,
            'until': None,
        }
        defaults.update(self.config)
        return defaults

    def _process(self):
        if self.crawl_type == self.CRAWL_TYPE_HANDLE_MESSAGES:
            self.crawl_tweets_with_twint()
            # self.crawl_tweets_with_api()
            self.populate_threads()
            self.crawl_reactions()
            self.crawl_relations()
            self.populate_users()
            self.crawl_profiles()
        elif self.crawl_type == self.CRAWL_TYPE_HASHTAG:
            self.crawl_tweets_with_twint()
            # self.crawl_tweets_with_api()
            self.populate_threads()
            self.populate_users()
            self.crawl_profiles()
        else:
            raise ValueError('unsupported crawl_type:%s' % self.crawl_type)

    def crawl_tweets_with_twint(self):
        from community.ingest.twitter.utils.twint_utils import CrawlBuffer

        if self.crawl_type == self.CRAWL_TYPE_HANDLE_MESSAGES:
            crawl_types = CrawlBuffer.HANDLE_CRAWL_TYPES
        elif self.crawl_type == self.CRAWL_TYPE_HASHTAG:
            crawl_types = CrawlBuffer.CRAWL_TYPE_HASHTAG
        else:
            raise ValueError('unsupported crawl_type:%s' % self.crawl_type)

        for crawl_type in crawl_types:
            crawl_buffer = CrawlBuffer(self, crawl_type, **self.cleaned_config)
            crawl_buffer.start_crawl()

    def crawl_tweets_with_api(self):
        pass

    def populate_threads(self):
        pass

    def crawl_reactions(self):
        from community.ingest.twitter.utils.api_utils import get_liking_users, object_to_dict

        new = Tweet.query(Tweet.id, Tweet.timestamp) \
                   .filter(Tweet.job == self)\
                   .all()
        objs = []
        for tweet_id, timestamp in tqdm(new):
            data = get_liking_users(tweet_id)
            for d in data:
                objs.append(TwitterReaction(
                    reaction=TwitterReaction.REACTION_TYPE_LIKE,
                    timestamp=timestamp,
                    job_id=self.id,
                    user_id=d.id,
                    data=d.data,
                    message_id=tweet_id
                ))
                if len(objs) > self.BULK_CREATE_CHUNK_SIZE:
                    TwitterReaction.bulk_upsert(objs)
                    objs = []
        if objs:
            TwitterReaction.bulk_upsert(objs)

    def crawl_relations(self):
        from community.ingest.twitter.utils.api_utils import get_user_followers, get_user_friends, object_to_dict

        users = TwitterHandle.query(TwitterHandle.id).all()
        objs = []
        for user_id in users:
            user_id = user_id[0]
            data = get_user_followers(user_id)
            for d in data:
                objs.append(TwitterRelation(
                    from_node_id=d.id,
                    relation_type=TwitterRelation.RELATION_TYPE_FOLLOWER,
                    to_node_id=user_id,
                    data=d.data,
                    timestamp=datetime.datetime.now(),
                    job_id=self.id,
                ))
                if len(objs) > self.BULK_CREATE_CHUNK_SIZE:
                    TwitterRelation.bulk_upsert(objs)
                    objs = []
        if objs:
            TwitterRelation.bulk_upsert(objs)

        # objs = []
        # for user_id in users:
        #     data = get_user_friends(user_id)
        #     for d in data:
        #         objs.append(TwitterRelation(
        #             from_node_id=d['user_id'],
        #             relation_type=TwitterRelation.RELATION_TYPE_FRIEND,
        #             to_node_id=user_id,
        #             timestamp=datetime.datetime.now(),
        #             job_id=self.id,
        #         ))
        #         if len(objs) > self.BULK_CREATE_CHUNK_SIZE:
        #             TwitterRelation.bulk_upsert(objs)
        #             objs = []
        # if objs:
        #     TwitterRelation.bulk_upsert(objs)

    def populate_users(self):
        existing = TwitterUser.query(TwitterUser.id).distinct()
        from_messages = Tweet.query(Tweet.user_id.label('id'),
                                    Tweet.data['username'].label('username'),
                                    Tweet.job_id) \
                             .filter(Tweet.user_id.notin_(existing),
                                     Tweet.job == self) \
                             .distinct()
        from_reactions = TwitterReaction.query(TwitterReaction.user_id.label('id'),
                                               TwitterReaction.data['username'].label('username'),
                                               TwitterReaction.job_id) \
                                        .filter(TwitterReaction.user_id.notin_(existing),
                                                TwitterReaction.job == self) \
                                        .distinct()
        from_relations = TwitterRelation.query(TwitterRelation.from_node_id.label('id'),
                                               TwitterRelation.data['username'].label('username'),
                                               TwitterRelation.job_id) \
                                        .filter(TwitterRelation.from_node_id.notin_(existing),
                                                TwitterRelation.job == self) \
                                        .distinct()
        from_all = from_messages.union(from_reactions, from_relations)

        cols = ['id', 'username', 'job_id']
        tu_table = self.metadata.tables[TwitterUser.__tablename__]
        insert_query = tu_table.insert().from_select(cols, from_all)
        session = self.session_factory()
        session.execute(insert_query)

        trimmed_username = func.substr(TwitterUser.username, 2, func.char_length(TwitterUser.username) - 2)
        TwitterUser.filter(TwitterUser.job == self, TwitterUser.username.like('"%"'))\
                   .update({'username':  trimmed_username}, synchronize_session='fetch')
        session.commit()

    def crawl_profiles(self):
        from community.ingest.twitter.utils.api_utils import get_users
        from community.platform.utils.iter_utils import chunkify

        users = TwitterUser.query(TwitterUser.id)\
                           .filter(TwitterUser.job == self)\
                           .all()
        users = list(itertools.chain.from_iterable(users))
        objs = []
        for user_id_set in chunkify(users, 100):
            user_id_set = ','.join(map(str, user_id_set))
            data = get_users(user_id_set)
            for d in data:
                objs.append(TwitterUser(
                    id=d['id'],
                    username=d['username'],
                    name=d['name'],
                    data=d.data,
                    job=self
                ))
                if len(objs) > self.BULK_CREATE_CHUNK_SIZE:
                    TwitterUser.bulk_update(objs)
                    objs = []
        if objs:
            TwitterUser.bulk_update(objs)


class TwitterUser(BaseUser):
    JOB_MODEL = TwitterJob


class Tweet(BaseMessage):
    JOB_MODEL = TwitterJob
    USER_MODEL = TwitterUser


class TwitterRelation(BaseRelation):
    JOB_MODEL = TwitterJob
    USER_MODEL = TwitterUser
    RELATION_TYPE_FRIEND = 'friend'
    RELATION_TYPE_FOLLOWER = 'follower'
    RELATION_TYPES = (
        (RELATION_TYPE_FRIEND, RELATION_TYPE_FRIEND.title()),
        (RELATION_TYPE_FOLLOWER, RELATION_TYPE_FOLLOWER.title())
    )


class TwitterReaction(BaseMessageReaction):
    JOB_MODEL = TwitterJob
    USER_MODEL = TwitterUser
    MESSAGE_MODEL = Tweet

    REACTION_TYPE_LIKE = 'like'
    REACTION_TYPES = (
        (REACTION_TYPE_LIKE, REACTION_TYPE_LIKE.title())
    )


class TwitterThread(BaseMessageThread):
    JOB_MODEL = TwitterJob
    MESSAGE_MODEL = Tweet
