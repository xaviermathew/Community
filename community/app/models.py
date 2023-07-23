from django.core.exceptions import FieldDoesNotExist
from django.db import models

from rainman import models as rm_models

from community.app import dj_models
from community import models as av_models


def get_av_object(dj_object):
    av_class = model_map[dj_object.__class__]
    return av_class.filter(av_class.id == dj_object.id).one()


model_map = dict([
    (dj_models.Discordchannel, av_models.DiscordChannel),
    (dj_models.Discordevent, av_models.DiscordEvent),
    (dj_models.Discordguild, av_models.DiscordGuild),
    (dj_models.Discordjob, av_models.DiscordJob),
    (dj_models.Discordmessage, av_models.DiscordMessage),
    (dj_models.Discordreaction, av_models.DiscordReaction),
    (dj_models.Discordthread, av_models.DiscordThread),
    (dj_models.Discorduser, av_models.DiscordUser),
    (dj_models.Project, av_models.Project),
    (dj_models.Projectmember, av_models.ProjectMember),
    (dj_models.Tweet, av_models.Tweet),
    (dj_models.Twitterhandle, av_models.TwitterHandle),
    (dj_models.Twitterjob, av_models.TwitterJob),
    (dj_models.Twitterreaction, av_models.TwitterReaction),
    (dj_models.Twitterrelation, av_models.TwitterRelation),
    (dj_models.Twitterthread, av_models.TwitterThread),
    (dj_models.Twitteruser, av_models.TwitterUser),
    (dj_models.Githubrepo, av_models.GithubRepo),
    (dj_models.Githubjob, av_models.GithubJob),
    (dj_models.Githubmessage, av_models.GithubMessage),
    (dj_models.Githubreaction, av_models.GithubReaction),
    (dj_models.Githubrelation, av_models.GithubRelation),
    (dj_models.Githubthread, av_models.GithubThread),
    (dj_models.Githubuser, av_models.GithubUser),
    (dj_models.User, av_models.User),
    (dj_models.RainmanCache, rm_models.Cache),
])
for dj_model, av_model in model_map.items():
    dj_model.__str__ = dj_model.__repr__ = av_model.__repr__
    try:
        dj_model._meta.get_field('id').primary_key = True
    except FieldDoesNotExist:
        pass

    col_map = av_model.__table__.c
    for field in dj_model._meta.fields:
        if isinstance(field, models.CharField):
            sqla_field = col_map[field.name].type
            field.max_length = sqla_field.length
            if hasattr(sqla_field, 'choices'):
                field.choices = sqla_field.choices

    if issubclass(av_model, av_models.BaseSource):
        dj_model.REPR_FIELD = av_model.REPR_FIELD

    dj_model.av_object = property(get_av_object)
