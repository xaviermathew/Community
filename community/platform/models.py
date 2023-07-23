import logging

from sqlalchemy import Column, Integer, Text, ForeignKey, func, literal
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from community.models import Base

_LOG = logging.getLogger(__name__)


class Project(Base):
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

    def __repr__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.name)

    def populate_users(self):
        from community.ingest.discord.models import DiscordUser, DiscordJob
        from community.ingest.github.models import GithubUser, GithubJob
        from community.ingest.twitter.models import TwitterUser, TwitterJob

        d_existing = User.query(User.discord_username)\
                         .filter(User.discord_username != None)\
                         .distinct()
        d_qs = DiscordUser.query(DiscordUser.username.label('discord_username'),
                                 literal(None).label('github_username'),
                                 literal(None).label('twitter_username'),
                                 DiscordUser.name,
                                 DiscordUser.data) \
                          .filter(DiscordUser.username.notin_(d_existing))\
                          .join(DiscordJob, DiscordUser.job_id == DiscordJob.id)\
                          .filter(DiscordJob.project == self)

        g_existing = User.query(User.github_username) \
                         .filter(User.github_username != None) \
                         .distinct()
        g_qs = GithubUser.query(literal(None).label('discord_username'),
                                GithubUser.username.label('github_username'),
                                literal(None).label('twitter_username'),
                                GithubUser.name,
                                GithubUser.data) \
                         .filter(GithubUser.username.notin_(g_existing))\
                         .join(GithubJob, GithubUser.job_id == GithubJob.id)\
                         .filter(GithubJob.project == self)

        t_existing = User.query(User.twitter_username)\
                         .filter(User.twitter_username != None) \
                         .distinct()
        t_qs = TwitterUser.query(literal(None).label('discord_username'),
                                 literal(None).label('github_username'),
                                 TwitterUser.username.label('twitter_username'),
                                 TwitterUser.name,
                                 TwitterUser.data) \
                          .filter(TwitterUser.username.notin_(t_existing))\
                          .join(TwitterJob, TwitterUser.job_id == TwitterJob.id)\
                          .filter(TwitterJob.project == self)
        new_users = d_qs.union_all(g_qs, t_qs)

        u_table = self.metadata.tables[User.__tablename__]
        cols = ['discord_username', 'github_username', 'twitter_username', 'name', 'data']
        insert_query = u_table.insert() \
                              .from_select(cols, new_users)
        session = self.session_factory()
        session.execute(insert_query)
        session.commit()


class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    discord_username = Column(Text)
    twitter_username = Column(Text)
    github_username = Column(Text)
    duplicate_of_id = Column(Integer, ForeignKey('user.id'))
    duplicate_of = relationship('User')
    data = Column(JSONB)

    def __repr__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.name)

    @classmethod
    def unique_users(cls):
        users = cls.filter(cls.duplicate_of_id.is_(None))
        dup_users = cls.filter().subquery()
        qs = users.join(dup_users, (cls.id == dup_users.c.duplicate_of_id) | (cls.id == dup_users.c.id))\
                  .with_entities(cls.id,
                                 cls.name,
                                 func.min(dup_users.c.discord_username).label('discord_username'),
                                 func.min(dup_users.c.twitter_username).label('twitter_username'),
                                 func.min(dup_users.c.github_username).label('github_username'))\
                  .group_by(cls.id, cls.name)
        return qs

    @classmethod
    def merge_user_hook(cls, user_id, final_id):
        # implement logic to delete or point objects with FK refs to final_id
        _LOG.info('user_id:[%s] final_id:[%s]', user_id, final_id)

    @classmethod
    def merge_all(cls):
        from community.platform.user_merge import merge

        users = cls.query(cls.id, cls.name, cls.discord_username, cls.twitter_username, cls.github_username)
        with_final = merge(users.all())
        for final, g_users in with_final:
            for d in g_users:
                cls.filter(cls.id == d['id'])\
                   .update({'duplicate_of_id': final.id}, synchronize_session='fetch')
                cls.merge_user_hook(d['id'], final.id)


class ProjectMember(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship('User')
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    project = relationship('Project')

    def __repr__(self):
        return '<%s - %s>' % (self.project.name, self.user.name)
