# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Discordchannel(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.TextField()
    guild = models.ForeignKey('Discordguild', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'discordchannel'


class Discordevent(models.Model):
    id = models.AutoField(primary_key=True)
    event = models.TextField()
    user_id = models.IntegerField(blank=True, null=True)
    data = models.JSONField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'discordevent'


class Discordguild(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.TextField()
    project = models.ForeignKey('Project', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'discordguild'


class Discordjob(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.JSONField()
    status = models.CharField()
    project = models.ForeignKey('Project', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'discordjob'


class Discordmessage(models.Model):
    id = models.BigIntegerField(primary_key=True)
    message = models.TextField()
    timestamp = models.DateTimeField()
    data = models.JSONField()
    user_id = models.IntegerField()
    channel = models.ForeignKey(Discordchannel, models.DO_NOTHING)
    job = models.ForeignKey(Discordjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'discordmessage'


class Discordreaction(models.Model):
    id = models.AutoField(primary_key=True)
    reaction = models.TextField()
    data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField()
    user_id = models.IntegerField()
    message_id = models.IntegerField()
    job = models.ForeignKey(Discordjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'discordreaction'


class Discordthread(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    parent_message_id = models.IntegerField()
    message_id = models.IntegerField()
    job = models.ForeignKey(Discordjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'discordthread'


class Discorduser(models.Model):
    id = models.BigIntegerField(primary_key=True)
    username = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    job = models.ForeignKey(Discordjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'discorduser'


class Githubevent(models.Model):
    event = models.TextField()
    user_id = models.BigIntegerField(blank=True, null=True)
    data = models.JSONField()
    timestamp = models.DateTimeField()
    id = models.BigIntegerField(primary_key=True)
    job = models.ForeignKey('Githubjob', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'githubevent'


class Githubjob(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.JSONField()
    status = models.CharField()
    project = models.ForeignKey('Project', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'githubjob'


class Githubmessage(models.Model):
    id = models.BigIntegerField(primary_key=True)
    message = models.TextField()
    timestamp = models.DateTimeField()
    data = models.JSONField()
    user_id = models.BigIntegerField()
    job = models.ForeignKey(Githubjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'githubmessage'


class Githubreaction(models.Model):
    id = models.BigIntegerField(primary_key=True)
    reaction = models.TextField()
    data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField()
    user_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    job = models.ForeignKey(Githubjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'githubreaction'


class Githubrelation(models.Model):
    id = models.AutoField(primary_key=True)
    from_node_id = models.BigIntegerField()
    to_node_id = models.BigIntegerField()
    data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField()
    relation_type = models.CharField()
    job = models.ForeignKey(Githubjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'githubrelation'


class Githubrepo(models.Model):
    id = models.BigIntegerField(primary_key=True)
    owner = models.TextField()
    name = models.TextField()
    project = models.ForeignKey('Project', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'githubrepo'


class Githubthread(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    parent_message_id = models.IntegerField()
    message_id = models.BigIntegerField()
    job = models.ForeignKey(Githubjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'githubthread'


class Githubuser(models.Model):
    id = models.BigIntegerField(primary_key=True)
    username = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    job = models.ForeignKey(Githubjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'githubuser'


class Project(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()

    class Meta:
        managed = False
        db_table = 'project'


class Projectmember(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING)
    project = models.ForeignKey(Project, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'projectmember'


class Tweet(models.Model):
    id = models.BigIntegerField(primary_key=True)
    message = models.TextField()
    timestamp = models.DateTimeField()
    data = models.JSONField()
    user_id = models.BigIntegerField()
    job = models.ForeignKey('Twitterjob', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'tweet'


class Twitterhandle(models.Model):
    id = models.BigIntegerField(primary_key=True)
    handle = models.TextField()
    project = models.ForeignKey(Project, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'twitterhandle'


class Twitterjob(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.JSONField()
    status = models.CharField()
    query = models.TextField()
    crawl_type = models.CharField()
    project = models.ForeignKey(Project, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'twitterjob'


class Twitterreaction(models.Model):
    id = models.AutoField(primary_key=True)
    reaction = models.TextField()
    data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField()
    user_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    job = models.ForeignKey(Twitterjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'twitterreaction'


class Twitterrelation(models.Model):
    id = models.AutoField(primary_key=True)
    from_node_id = models.BigIntegerField()
    to_node_id = models.BigIntegerField()
    data = models.JSONField(blank=True, null=True)
    relation_type = models.CharField()
    job = models.ForeignKey(Twitterjob, models.DO_NOTHING)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'twitterrelation'


class Twitterthread(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    parent_message_id = models.IntegerField()
    message_id = models.BigIntegerField()
    job = models.ForeignKey(Twitterjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'twitterthread'


class Twitteruser(models.Model):
    id = models.BigIntegerField(primary_key=True)
    username = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    job = models.ForeignKey(Twitterjob, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'twitteruser'


class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    discord_username = models.TextField(blank=True, null=True)
    twitter_username = models.TextField(blank=True, null=True)
    github_username = models.TextField(blank=True, null=True)
    duplicate_of = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    data = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user'


class RainmanCache(models.Model):
    prefix = models.CharField(max_length=50)
    key = models.TextField()
    key_hash = models.CharField(primary_key=True, max_length=100)
    value = models.JSONField(blank=True, null=True)
    created_on = models.DateTimeField()
    modified_on = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'rainman_cache'
