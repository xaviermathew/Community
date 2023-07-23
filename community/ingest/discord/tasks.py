from community.app.celery import app as celery_app


@celery_app.task(ignore_result=True)
def save_discord_event(event_name, d):
    from community.ingest.discord.utils.bot_client import BotClient
    BotClient.save_event(event_name, d)
