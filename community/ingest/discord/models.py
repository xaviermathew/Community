import copy
from functools import cached_property
import json
import os

from discord.channel import TextChannel
from sqlalchemy import ForeignKey, Column, Integer, Text, literal, func, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression
from tqdm import tqdm

from community.app import settings
from community.models import Base
from community.ingest.base.models import BaseJob, BaseSource, BaseUser, BaseMessage, BaseMessageReaction,\
    BaseMessageThread, BaseEvent


class DiscordAPIObjectMixin(object):
    _CLIENT = None

    @classmethod
    async def get_client(cls):
        from community.ingest.discord.utils.bot_client import BotClient

        if DiscordAPIObjectMixin._CLIENT is None:
            client = BotClient()
            await client.login(settings.DISCORD_BOT_TOKEN)
            DiscordAPIObjectMixin._CLIENT = client
        return DiscordAPIObjectMixin._CLIENT

    @property
    async def discord_object(self):
        raise NotImplementedError


class DiscordGuild(BaseSource, DiscordAPIObjectMixin):
    REPR_FIELD = 'name'
    INTERESTING_CHANNELS = [
        TextChannel
    ]

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    name = Column(Text, nullable=False)
    channels = relationship('DiscordChannel', back_populates='guild')

    @cached_property
    async def discord_object(self):
        client = await self.get_client()
        return await client.fetch_guild(self.id)

    @classmethod
    async def discover_guilds(cls, project):
        from community.platform.models import Project

        client = await cls.get_client()
        project_id = project.id if isinstance(project, Project) else project
        async for g in client.fetch_guilds():
            dg = DiscordGuild.get_or_create(id=g.id, name=g.name, project_id=project_id)
            await dg.discover_channels()

    async def discover_channels(self):
        obj = await self.discord_object
        channels = await obj.fetch_channels()
        for ch in channels:
            if any([isinstance(ch, klass) for klass in self.INTERESTING_CHANNELS]):
                DiscordChannel.get_or_create(id=ch.id, name=ch.name, guild_id=self.id)

    def crawl_messages(self, **kwargs):
        for ch in self.channels:
            ch.crawl_messages()


class DiscordChannel(Base, DiscordAPIObjectMixin):
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    name = Column(Text, nullable=False)
    guild_id = Column(BigInteger, ForeignKey('discordguild.id'), nullable=False)
    guild = relationship('DiscordGuild')

    def __repr__(self):
        return '<%s:%s DiscordGuild:%s>' % (self.__class__.__name__, self.name, self.guild.name)

    @cached_property
    async def discord_object(self):
        client = await self.get_client()
        return await client.fetch_channel(self.id)

    def crawl_messages(self, **kwargs):
        config = {'guild_id': self.guild_id, 'channel_id': self.id}
        DiscordJob.add_job(project_id=self.guild.project_id, config=config)


class DiscordJob(BaseJob):
    def start_crawl_with_discord_scraper(self):
        from community.ingest.discord.utils.scraper.discord import getLastMessageGuild, start
        from community.ingest.discord.utils.scraper.module.DiscordScraper import DiscordScraper
        from community.ingest.discord.utils.scraper.module.utils import parse_timestamp, DEFAULT_CONFIG

        config = copy.deepcopy(DEFAULT_CONFIG)
        guild_id = self.config['guild_id']
        channel_id = self.config['channel_id']
        config['guilds'] = {guild_id: [channel_id]}

        discordscraper = DiscordScraper(configdata=config, tokenfiledata=settings.DISCORD_BEARER_TOKEN)
        last_msg_date = getLastMessageGuild(discordscraper, guild_id, channel_id)
        end_date = DiscordMessage.query(func.max(DiscordMessage.timestamp)).one()[0]
        start(discordscraper, guild_id, channel_id, day=last_msg_date, end_date=end_date)

        g = DiscordGuild.filter(DiscordGuild.id == guild_id).one()
        ch = DiscordChannel.filter(DiscordChannel.id == channel_id).one()
        dirpath = 'cached/%s_%s/%s_%s' % (g.id, g.name, channel_id, ch.name)
        msgs = []
        for fname in tqdm(os.listdir(dirpath)):
            fpath = os.path.join(dirpath, fname)
            data = json.load(open(fpath))
            for d in data['messages']:
                msgs.extend(d)

        objs = []
        for d in msgs:
            objs.append(DiscordMessage(job=self,
                                       id=int(d['id']),
                                       message=d['content'],
                                       timestamp=parse_timestamp(d['timestamp']),
                                       user_id=int(d['author']['id']),
                                       channel_id=int(d['channel_id']),
                                       data=d))
        DiscordMessage.bulk_create(objs)

    async def start_crawl_with_discordpy(self):
        channel_id = self.config['channel_id']
        ch = DiscordChannel.filter(DiscordChannel.id == channel_id).one()
        obj = await ch.discord_object
        objs = []
        async for m in obj.history():
            objs.append(DiscordMessage(job=self,
                                       id=m.id,
                                       message=m.content,
                                       timestamp=m.edited_at or m.created_at,
                                       user_id=m.author.id,
                                       channel_id=m.channel.id,
                                       data={}))
        DiscordMessage.bulk_create(objs)

    def populate_threads(self):
        pass

    def populate_reactions(self):
        existing = DiscordReaction.query(DiscordReaction.message_id,
                                         DiscordReaction.reaction,
                                         DiscordReaction.user_id)
        message_id = DiscordEvent.data['message_id'].cast(Text).cast(BigInteger)
        reaction = DiscordEvent.data['emoji']['name'].cast(Text)
        new = DiscordEvent.query(DiscordEvent.user_id,
                                 reaction.label('reaction'),
                                 DiscordEvent.timestamp,
                                 message_id.label('message_id'),
                                 literal(self.id).label('job_id')) \
                          .filter(expression.tuple_(message_id,
                                                    reaction,
                                                    DiscordEvent.user_id).notin_(existing),
                                  DiscordEvent.event == 'MESSAGE_REACTION_ADD')
        table = DiscordReaction.metadata.tables[DiscordReaction.__tablename__]
        insert_query = table.insert()\
                            .from_select(['user_id', 'reaction', 'timestamp', 'message_id', 'job_id'],
                                         new)
        session = self.session_factory()
        session.execute(insert_query)
        session.commit()

    def populate_users(self):
        existing = DiscordUser.query(DiscordUser.id).distinct()
        from_messages = DiscordMessage.query(DiscordMessage.user_id.label('id'),
                                             DiscordMessage.data['author']['username'].label('username'),
                                             DiscordMessage.job_id) \
                                      .filter(DiscordMessage.user_id.notin_(existing),
                                              DiscordMessage.job == self) \
                                      .distinct()
        from_reactions = DiscordReaction.query(DiscordReaction.user_id.label('id'),
                                               DiscordReaction.data['author']['username'].label('username'),
                                               DiscordReaction.job_id) \
                                        .filter(DiscordReaction.user_id.notin_(existing),
                                                DiscordReaction.job == self) \
                                        .distinct()
        from_all = from_messages.union(from_reactions)

        du_table = self.metadata.tables[DiscordUser.__tablename__]
        cols = ['id', 'username', 'job_id']
        insert_query = du_table.insert().from_select(cols, from_all)
        session = self.session_factory()
        session.execute(insert_query)

        trimmed_username = func.substr(DiscordUser.username, 2, func.char_length(DiscordUser.username) - 2)
        DiscordUser.filter(DiscordUser.job == self, DiscordUser.username.like('"%"')) \
                   .update({'username': trimmed_username}, synchronize_session='fetch')
        session.commit()

    def _process(self):
        # self.start_crawl_with_discord_scraper()
        self.start_crawl_with_discordpy()
        self.populate_threads()
        self.populate_reactions()
        self.populate_users()


class DiscordUser(BaseUser):
    JOB_MODEL = DiscordJob


class DiscordMessage(BaseMessage, DiscordAPIObjectMixin):
    JOB_MODEL = DiscordJob
    USER_MODEL = DiscordUser

    channel_id = Column(Integer, ForeignKey('discordchannel.id'), nullable=False)
    channel = relationship('DiscordChannel')

    @cached_property
    async def discord_object(self):
        ch = DiscordChannel.filter(DiscordChannel.id == self.channel_id).one()
        obj = await ch.discord_object
        return await obj.fetch_message(self.id)


class DiscordReaction(BaseMessageReaction):
    JOB_MODEL = DiscordJob
    USER_MODEL = DiscordUser
    MESSAGE_MODEL = DiscordMessage


class DiscordEvent(BaseEvent):
    id = Column(BigInteger, primary_key=True)


class DiscordThread(BaseMessageThread):
    JOB_MODEL = DiscordJob
    MESSAGE_MODEL = DiscordMessage
