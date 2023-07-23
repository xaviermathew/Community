import logging

from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy_utils import ChoiceType

from community.models import Base

_LOG = logging.getLogger(__name__)


class BaseJob(Base):
    __abstract__ = True

    STATUS_NEW = 'new'
    STATUS_RUNNING = 'running'
    STATUS_DONE = 'done'
    STATUS_ERROR = 'error'
    STATUS_TYPES = (
        (STATUS_NEW, STATUS_NEW.title()),
        (STATUS_RUNNING, STATUS_RUNNING.title()),
        (STATUS_DONE, STATUS_DONE.title()),
        (STATUS_ERROR, STATUS_ERROR.title())
    )

    id = Column(Integer, primary_key=True)

    @declared_attr
    def project_id(cls):
        return Column(Integer, ForeignKey('project.id'), nullable=False)

    @declared_attr
    def project(cls):
        return relationship('Project')

    config = Column(JSONB, nullable=False)
    status = Column(ChoiceType(STATUS_TYPES, impl=String(25)), default=STATUS_NEW, nullable=False)

    def __repr__(self):
        return '<%s:%s:%s - %s>' % (self.__class__.__name__, self.project.name, self.config, self.status)

    @property
    def cleaned_config(self):
        raise NotImplementedError

    @classmethod
    def add_job(cls, project_id, **kwargs):
        job = cls.create(project_id=project_id, **kwargs)
        job.process()

    def _process(self):
        raise NotImplementedError

    def process(self):
        _LOG.info('starting crawl for %s', self)
        with self.saving():
            self.status = self.STATUS_RUNNING
        # session = session_factory()
        # self.status = self.STATUS_RUNNING
        # session.commit()

        # try:
        #     self._process()
        # except Exception as ex:
        #     _LOG.exception('error crawling %s - %s', self, ex)
        #     status = self.STATUS_ERROR
        # else:
        #     status = self.STATUS_DONE
        self._process()
        status = self.STATUS_DONE

        with self.saving():
            self.status = status
        # self.status = status
        # session.commit()


class BaseSource(Base):
    __abstract__ = True

    REPR_FIELD = None

    @declared_attr
    def project_id(cls):
        return Column(Integer, ForeignKey('project.id'), nullable=False)

    @declared_attr
    def project(cls):
        return relationship('Project')

    def __repr__(self):
        return '<%s:%s Project:%s>' % (self.__class__.__name__, getattr(self, self.REPR_FIELD), self.project.name)

    def crawl_messages(self, **kwargs):
        raise NotImplementedError


class BaseUser(Base):
    __abstract__ = True

    JOB_MODEL = None

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    username = Column(Text)
    name = Column(Text)
    data = Column(JSONB)

    @declared_attr
    def job_id(cls):
        return Column(Integer, ForeignKey('%s.id' % cls.JOB_MODEL.__name__.lower()), nullable=False)

    @declared_attr
    def job(cls):
        return relationship(cls.JOB_MODEL.__name__)

    def __repr__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.username)


class BaseMessage(Base):
    __abstract__ = True

    JOB_MODEL = None
    USER_MODEL = None

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    data = Column(JSONB, nullable=False)

    @declared_attr
    def job_id(cls):
        return Column(Integer, ForeignKey('%s.id' % cls.JOB_MODEL.__name__.lower()), nullable=False)

    @declared_attr
    def job(cls):
        return relationship(cls.JOB_MODEL.__name__)

    # @declared_attr
    # def user_id(cls):
    #     return Column(BigInteger, ForeignKey('%s.id' % cls.USER_MODEL.__name__.lower()), nullable=False)

    # @declared_attr
    # def user(cls):
    #     return relationship(cls.USER_MODEL.__name__)

    user_id = Column(BigInteger, nullable=False)

    def __repr__(self):
        return '<%s:"%s" ON "%s">' % (self.__class__.__name__, self.message, self.timestamp)


class BaseRelation(Base):
    __abstract__ = True

    JOB_MODEL = None
    USER_MODEL = None
    RELATION_TYPES = None

    id = Column(Integer, primary_key=True)

    # @declared_attr
    # def from_node_id(cls):
    #     return Column(BigInteger, ForeignKey('%s.id' % cls.USER_MODEL.__name__.lower()), nullable=False)

    # @declared_attr
    # def to_node_id(cls):
    #     return Column(BigInteger, ForeignKey('%s.id' % cls.USER_MODEL.__name__.lower()), nullable=False)

    # @declared_attr
    # def from_node(cls):
    #     return relationship(cls.USER_MODEL.__name__)

    # @declared_attr
    # def to_node(cls):
    #     return relationship(cls.USER_MODEL.__name__)

    from_node_id = Column(BigInteger, nullable=False)
    to_node_id = Column(BigInteger, nullable=False)

    @declared_attr
    def relation_type(cls):
        return Column(ChoiceType(cls.RELATION_TYPES, impl=String(25)), nullable=False)

    @declared_attr
    def job_id(cls):
        return Column(Integer, ForeignKey('%s.id' % cls.JOB_MODEL.__name__.lower()), nullable=False)

    @declared_attr
    def job(cls):
        return relationship(cls.JOB_MODEL.__name__)

    data = Column(JSONB)
    timestamp = Column(DateTime, nullable=False)

    def __repr__(self):
        return '<%s:(%s)-[%s]->(%s)>' % (self.__class__.__name__, self.from_node_id, self.relation_type, self.to_node_id)


class BaseMessageReaction(Base):
    __abstract__ = True

    JOB_MODEL = None
    USER_MODEL = None
    MESSAGE_MODEL = None

    id = Column(Integer, primary_key=True)
    reaction = Column(Text, nullable=False)
    data = Column(JSONB)
    timestamp = Column(DateTime, nullable=False)

    @declared_attr
    def job_id(cls):
        return Column(Integer, ForeignKey('%s.id' % cls.JOB_MODEL.__name__.lower()), nullable=False)

    @declared_attr
    def job(cls):
        return relationship(cls.JOB_MODEL.__name__)

    # @declared_attr
    # def user_id(cls):
    #     return Column(BigInteger, ForeignKey('%s.id' % cls.USER_MODEL.__name__.lower()), nullable=False)

    # @declared_attr
    # def user(cls):
    #     return relationship(cls.USER_MODEL.__name__)

    user_id = Column(BigInteger, nullable=False)

    # @declared_attr
    # def message_id(cls):
    #     return Column(BigInteger, ForeignKey('%s.id' % cls.MESSAGE_MODEL.__name__.lower()), nullable=False)

    # @declared_attr
    # def message(cls):
    #     return relationship(cls.MESSAGE_MODEL.__name__)

    message_id = Column(BigInteger, nullable=False)

    def __repr__(self):
        return '<%s:"%s" ON "%s">' % (self.__class__.__name__, self.reaction, self.timestamp)


class BaseMessageThread(Base):
    __abstract__ = True

    JOB_MODEL = None
    MESSAGE_MODEL = None

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)

    @declared_attr
    def job_id(cls):
        return Column(Integer, ForeignKey('%s.id' % cls.JOB_MODEL.__name__.lower()), nullable=False)

    @declared_attr
    def job(cls):
        return relationship(cls.JOB_MODEL.__name__)

    # @declared_attr
    # def parent_message_id(cls):
    #     return Column(Integer, ForeignKey('%s.id' % cls.MESSAGE_MODEL.__name__.lower()), nullable=False)

    # @declared_attr
    # def parent_message(cls):
    #     return relationship(cls.MESSAGE_MODEL.__name__)

    parent_message_id = Column(Integer, nullable=False)

    # @declared_attr
    # def message_id(cls):
    #     return Column(BigInteger, ForeignKey('%s.id' % cls.MESSAGE_MODEL.__name__.lower()), nullable=False)

    # @declared_attr
    # def message(cls):
    #     return relationship(cls.MESSAGE_MODEL.__name__)

    message_id = Column(BigInteger, nullable=False)

    def __repr__(self):
        return '<%s:%s -> %s>' % (self.__class__.__name__, self.parent_message_id, self.message_id)


class BaseEvent(Base):
    __abstract__ = True

    event = Column(Text, nullable=False, index=True)
    user_id = Column(BigInteger)
    data = Column(JSONB, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    def __repr__(self):
        return '<%s:%s - %s>' % (self.__class__.__name__, self.event, self.data)
