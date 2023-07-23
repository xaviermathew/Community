import itertools

from elasticsearch_dsl import Q
from sqlalchemy import Column, Text, Integer, ForeignKey, func, BigInteger
from sqlalchemy.sql import functions
from sqlalchemy.orm import relationship

from community.ingest.base.models import BaseSource, BaseJob, BaseMessageReaction, BaseRelation,\
    BaseMessage, BaseUser, BaseMessageThread, BaseEvent


class GithubRepo(BaseSource):
    REPR_FIELD = 'name'

    # github-gha-repos
    """
    ownerid
    repo_id
    owner
    name
    created_at
    updated_at
    timestamp
    url
    homeurl
    sshurl
    """

    # github-repo-history
    """
    timestamp
    owner
    name
    repo_id
    starscount
    watcherscount
    issuescount
    """

    id = Column(Integer, primary_key=True, autoincrement=False)
    owner = Column(Text, nullable=False)
    name = Column(Text, nullable=False)

    def crawl_messages(self):
        config = {'id': self.id, 'owner': self.owner, 'name': self.name}
        GithubJob.add_job(project_id=self.project_id, config=config)


class GithubJob(BaseJob):
    BULK_CREATE_CHUNK_SIZE = 1000

    def __repr__(self):
        return '<%s:%s:%s - %s>' % (self.__class__.__name__, self.project.name, self.config, self.status)

    def _filter_by_date(self, qs, model):
        session = self.session_factory()
        try:
            max_ts = session.query(model) \
                            .with_entities(functions.max(model.timestamp)).one()[0]
        except IndexError:
            max_ts = None

        if max_ts is not None:
            qs = qs.filter('range', timestamp={'gte': max_ts})
        return qs

    def populate_project(self):
        pass

    def populate_events(self):
        from community.platform.utils.search_utils import get_search, serialize_search_results
        from community.ingest.github.utils import parse_timestamp

        repo_id = self.config['id']
        qs = get_search('github-gha-events')
        qs = self._filter_by_date(qs, GithubEvent)

        q_set = [
            Q('term', repo_id=repo_id),
            Q('term', prrepo_id=repo_id),
            Q('term', forkrepo_id=repo_id),
        ]
        qs = qs.filter('bool', should=q_set)
        objs = []
        for d in serialize_search_results(qs.scan()):
            objs.append(GithubEvent(job=self,
                                    id=int(d.pop('id')),
                                    event=d.pop('event'),
                                    user_id=int(d.pop('user_id')),
                                    timestamp=parse_timestamp(d.pop('timestamp')),
                                    data={k: v for k, v in d.items() if d.get(k)}))
        GithubEvent.bulk_create(objs)

    def populate_relations(self):
        from community.platform.utils.search_utils import get_search, serialize_search_results
        from community.ingest.github.utils import parse_timestamp

        repo_id = self.config['id']
        qs = get_search('github-repo-user-stat')
        qs = self._filter_by_date(qs, GithubRelation)

        repo_q = Q('term', repo_id=repo_id)
        q_set = [
            Q('term', watching=True),
            Q('term', starred=True),
            Q('term', forked=True),
        ]
        qs = qs.filter('bool', must=repo_q, should=q_set)
        objs = []
        for d in serialize_search_results(qs.scan()):
            relation_types = []
            for relation_type in ['watching', 'starred', 'forked']:
                if d.pop(relation_type, False):
                    relation_types.append(relation_type)

            from_node_id = int(d.pop('user_id'))
            to_node_id = int(d.pop('repo_id'))
            timestamp = parse_timestamp(d.pop('timestamp'))
            for relation_type in relation_types:
                objs.append(GithubRelation(job=self,
                                           from_node_id=from_node_id,
                                           to_node_id=to_node_id,
                                           relation_type=relation_type,
                                           timestamp=timestamp,
                                           data={k: v for k, v in d.items() if d.get(k)}))
        GithubRelation.bulk_create(objs)

    def populate_messages(self):
        from community.platform.utils.search_utils import get_search, serialize_search_results
        from community.ingest.github.utils import parse_timestamp

        repo_id = self.config['id']
        qs = get_search(['github-gha-issues', 'github-gha-comments'])
        qs = self._filter_by_date(qs, GithubMessage)

        repo_q = Q('term', repo_id=repo_id)
        qs = qs.filter('bool', must=repo_q)
        objs = []
        for d in serialize_search_results(qs.scan()):
            title = d.pop('title', '')
            body = d.pop('body', '')
            objs.append(GithubMessage(job=self,
                                      id=int(d.pop('id')),
                                      message=title or body,
                                      timestamp=parse_timestamp(d.pop('timestamp')),
                                      user_id=d.pop('user_id'),
                                      data={k: v for k, v in d.items() if d.get(k)}))
        GithubMessage.bulk_create(objs)

    def populate_threads(self):
        pass

    def populate_users(self):
        existing = GithubUser.query(GithubUser.id).distinct()
        from_events = GithubEvent.query(GithubEvent.user_id.label('id'),
                                        GithubEvent.job_id) \
                                 .filter(GithubEvent.user_id.notin_(existing),
                                         GithubEvent.job == self) \
                                 .distinct()
        from_messages = GithubMessage.query(GithubMessage.user_id.label('id'),
                                            GithubMessage.job_id) \
                                     .filter(GithubMessage.user_id.notin_(existing),
                                             GithubMessage.job == self) \
                                     .distinct()
        from_relations = GithubRelation.query(GithubRelation.from_node_id.label('id'),
                                              GithubRelation.job_id) \
                                       .filter(GithubRelation.from_node_id.notin_(existing),
                                               GithubRelation.job == self) \
                                       .distinct()
        from_all = from_events.union(from_messages, from_relations)

        gu_table = self.metadata.tables[GithubUser.__tablename__]
        cols = ['id', 'job_id']
        insert_query = gu_table.insert().from_select(cols, from_all)
        session = self.session_factory()
        session.execute(insert_query)

        trimmed_username = func.substr(GithubUser.username, 2, func.char_length(GithubUser.username) - 2)
        GithubUser.filter(GithubUser.job == self, GithubUser.username.like('"%"')) \
                  .update({'username': trimmed_username}, synchronize_session='fetch')
        session.commit()

    def _crawl_profiles(self, users):
        from community.platform.utils.search_utils import get_search, serialize_search_results

        qs = get_search('github-gha-users')
        q_set = [Q('term', user_id=user_id) for user_id in users]
        qs = qs.filter('bool', should=q_set)
        yield from serialize_search_results(qs.scan())

    def crawl_profiles(self):
        from community.platform.utils.iter_utils import chunkify

        users = GithubUser.query(GithubUser.id) \
                          .filter(GithubUser.job == self) \
                          .all()
        users = list(itertools.chain.from_iterable(users))
        objs = []
        for user_id_set in chunkify(users, 1000):
            data = self._crawl_profiles(user_id_set)
            for d in data:
                objs.append(GithubUser(
                    id=d.pop('user_id'),
                    username=d.pop('login'),
                    name=d.pop('name', ''),
                    data={k: v for k, v in d.items() if d.get(k)},
                    job=self
                ))
                if len(objs) > self.BULK_CREATE_CHUNK_SIZE:
                    GithubUser.bulk_update(objs)
                    objs = []
        if objs:
            GithubUser.bulk_update(objs)

    def _process(self):
        self.populate_project()
        self.populate_events()
        self.populate_relations()
        self.populate_messages()
        self.populate_threads()
        self.populate_users()
        self.crawl_profiles()


class GithubUser(BaseUser):
    # github-gha-users
    """
    user_id
    twitterhandle
    name
    created_at
    updated_at
    login
    company
    email
    timestamp
    url
    websiteurl
    location
    """

    JOB_MODEL = GithubJob


class GithubMessage(BaseMessage):
    # github-gha-issues
    """
    created_at
    title
    body
    updated_at
    id
    timestamp
    closed_at
    user_id
    repo_id
    """

    # github-gha-comments
    """
    created_at
    body
    updated_at
    id
    timestamp
    issue_id
    user_id
    repo_id
    """

    JOB_MODEL = GithubJob
    USER_MODEL = GithubUser


class GithubRelation(BaseRelation):
    # github-repo-user-stat
    """
    pr_reviewed
    association
    watching
    issue_commented
    starred
    last_activity_at
    timestamp
    pr_merged
    pr_raised
    issue_raised
    starredat
    user_id
    pr_commented
    repo_id
    pushed
    forked
    """

    JOB_MODEL = GithubJob
    USER_MODEL = GithubUser
    RELATION_TYPE_WATCHING = 'watching'
    RELATION_TYPE_STARRED = 'starred'
    RELATION_TYPE_FORKED = 'forked'
    RELATION_TYPES = (
        (RELATION_TYPE_WATCHING, RELATION_TYPE_WATCHING.title()),
        (RELATION_TYPE_STARRED, RELATION_TYPE_STARRED.title()),
        (RELATION_TYPE_FORKED, RELATION_TYPE_FORKED.title())
    )


class GithubReaction(BaseMessageReaction):
    JOB_MODEL = GithubJob
    USER_MODEL = GithubUser
    MESSAGE_MODEL = GithubMessage


class GithubThread(BaseMessageThread):
    JOB_MODEL = GithubJob
    MESSAGE_MODEL = GithubMessage


class GithubEvent(BaseEvent):
    # github-gha-events
    """
    body
    orglogin
    id
    published_at
    closed_at
    merged_at
    prrepo_id
    user_id
    repo_id
    org_id
    created_at
    forkrepo_id
    title
    updated_at
    commentid
    timestamp
    owner
    """

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    job_id = Column(Integer, ForeignKey('githubjob.id'), nullable=False)
    job = relationship('GithubJob')
