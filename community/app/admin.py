from django.apps import apps
from django.contrib import admin, messages
from django.db import models
from django.forms import widgets

from community.app import dj_models


class BaseAdmin(admin.ModelAdmin):
    formfield_overrides = {models.TextField: {'widget': widgets.TextInput}}


class BaseMessageAdmin(BaseAdmin):
    list_display = ['user_id', 'message', 'timestamp']
    list_filter = ['job']


class BaseJobAdmin(BaseAdmin):
    list_display = ['status', 'project', 'config']
    list_filter = ['status']
    actions = ['process']

    def process(self, request, qs):
        messages.add_message(request, messages.INFO, 'Processing for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.process()


class BaseUserAdmin(BaseAdmin):
    list_display = ['id', 'username', 'name']
    list_filter = ['job']
    search_fields = ['id', 'username', 'name']


class BaseSourceAdmin(BaseAdmin):
    actions = ['crawl_messages']

    def crawl_messages(self, request, qs):
        messages.add_message(request, messages.INFO, 'Crawl for [%s] source(s) has been queued' % len(qs))
        for th in qs:
            th.av_object.crawl_messages()


class BaseReactionAdmin(BaseAdmin):
    list_display = ['message_id', 'reaction', 'timestamp']
    list_filter = ['reaction', 'job']


@admin.register(dj_models.Project)
class ProjectAdmin(BaseAdmin):
    list_display = ['name']
    actions = ['populate_users']

    def populate_users(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_users for [%s] project(s) has been queued' % len(qs))
        for th in qs:
            th.av_object.populate_users()


@admin.register(dj_models.User)
class UserAdmin(BaseAdmin):
    search_fields = ['name', 'discord_username', 'github_username', 'twitter_username']
    list_display = ['id', 'name', 'discord_username', 'github_username', 'twitter_username', 'duplicate_of']
    raw_id_fields = ['duplicate_of']


@admin.register(dj_models.RainmanCache)
class RainmanCacheAdmin(BaseAdmin):
    list_display = ['prefix', 'key', 'created_on']
    list_filter = ['prefix']


@admin.register(dj_models.Twitteruser)
class TwitterUserAdmin(BaseUserAdmin):
    pass


@admin.register(dj_models.Tweet)
class TweetAdmin(BaseMessageAdmin):
    pass


@admin.register(dj_models.Twitterreaction)
class TwitterReactionAdmin(BaseReactionAdmin):
    list_display = ['user_name', 'name'] + BaseReactionAdmin.list_display

    def name(self, obj):
        return obj.data.get('name')

    def user_name(self, obj):
        return obj.data.get('username')


@admin.register(dj_models.Twitterrelation)
class TwitterRelationAdmin(BaseAdmin):
    list_display = ['user_name', 'name', 'relation_type', 'to_node_id', 'timestamp']
    list_filter = ['relation_type', 'job']

    def name(self, obj):
        return obj.data.get('name')

    def user_name(self, obj):
        return obj.data.get('username')


@admin.register(dj_models.Twitterjob)
class TwitterJobAdmin(BaseJobAdmin):
    list_display = ['query', 'crawl_type'] + BaseJobAdmin.list_display
    list_filter = ['crawl_type'] + BaseJobAdmin.list_filter
    actions = BaseJobAdmin.actions + [
        'crawl_tweets', 'populate_threads', 'crawl_reactions',
        'crawl_relations', 'populate_users', 'crawl_profiles'
    ]

    def crawl_tweets(self, request, qs):
        messages.add_message(request, messages.INFO, 'crawl_tweets for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.crawl_tweets_with_twint()

    def populate_threads(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_threads for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_threads()

    def crawl_reactions(self, request, qs):
        messages.add_message(request, messages.INFO, 'crawl_reactions for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.crawl_reactions()

    def crawl_relations(self, request, qs):
        messages.add_message(request, messages.INFO, 'crawl_relations for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.crawl_relations()

    def populate_users(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_users for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_users()

    def crawl_profiles(self, request, qs):
        messages.add_message(request, messages.INFO, 'crawl_profiles for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.crawl_profiles()


@admin.register(dj_models.Twitterhandle)
class TwitterHandleAdmin(BaseSourceAdmin):
    list_display = ['handle', 'project']


@admin.register(dj_models.Discordguild)
class DiscordGuildAdmin(BaseSourceAdmin):
    list_display = ['name', 'id', 'project']


@admin.register(dj_models.Discordchannel)
class DiscordChannelAdmin(BaseSourceAdmin):
    list_display = ['name', 'id', 'guild']


@admin.register(dj_models.Discordjob)
class DiscordJobAdmin(BaseJobAdmin):
    actions = BaseJobAdmin.actions + [
        'crawl_messages', 'populate_threads', 'populate_reactions',
        'populate_users'
    ]

    def crawl_messages(self, request, qs):
        messages.add_message(request, messages.INFO, 'crawl_tweets for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.start_crawl_with_discordpy()

    def populate_threads(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_threads for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_threads()

    def populate_reactions(self, request, qs):
        messages.add_message(request, messages.INFO, 'crawl_reactions for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_reactions()

    def populate_users(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_users for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_users()


@admin.register(dj_models.Discordevent)
class DiscordEventAdmin(BaseAdmin):
    list_display = ['event', 'user_id', 'timestamp']
    list_filter = ['event']


@admin.register(dj_models.Discordmessage)
class DiscordMessageAdmin(BaseMessageAdmin):
    list_display = ['channel'] + BaseMessageAdmin.list_display


@admin.register(dj_models.Discorduser)
class DiscordUserAdmin(BaseUserAdmin):
    pass


@admin.register(dj_models.Discordreaction)
class DiscordReactionAdmin(BaseReactionAdmin):
    pass


@admin.register(dj_models.Githubrepo)
class GithubRepoAdmin(BaseSourceAdmin):
    list_display = ['owner', 'name', 'id', 'project']


@admin.register(dj_models.Githubjob)
class GithubJobAdmin(BaseJobAdmin):
    actions = BaseJobAdmin.actions + [
        'populate_project', 'populate_events', 'populate_relations',
        'populate_messages', 'populate_threads', 'populate_users',
        'crawl_profiles'
    ]

    def populate_project(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_project for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_project()

    def populate_events(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_events for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_events()

    def populate_relations(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_relations for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_relations()

    def populate_messages(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_messages for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_messages()

    def populate_threads(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_threads for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_threads()

    def populate_users(self, request, qs):
        messages.add_message(request, messages.INFO, 'populate_users for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.populate_users()

    def crawl_profiles(self, request, qs):
        messages.add_message(request, messages.INFO, 'crawl_profiles for [%s] jobs(s) has been queued' % len(qs))
        for tj in qs:
            tj.av_object.crawl_profiles()


@admin.register(dj_models.Githubevent)
class GithubEventAdmin(BaseAdmin):
    list_display = ['event', 'user_id', 'repo_id', 'org_id', 'timestamp']
    list_filter = ['event', 'job']

    def repo_id(self, obj):
        return obj.data.get('repo_id')

    def org_id(self, obj):
        return obj.data.get('org_id')


@admin.register(dj_models.Githubmessage)
class GithubMessageAdmin(BaseMessageAdmin):
    pass


@admin.register(dj_models.Githubuser)
class GithubUserAdmin(BaseUserAdmin):
    pass


@admin.register(dj_models.Githubreaction)
class GithubReactionAdmin(BaseReactionAdmin):
    list_filter = ['job']


@admin.register(dj_models.Githubrelation)
class GithubRelationAdmin(BaseAdmin):
    list_display = ['from_node_id', 'relation_type', 'to_node_id', 'timestamp']
    list_filter = ['relation_type', 'job']


for model in apps.get_models():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
