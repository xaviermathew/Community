import typer

app = typer.Typer()


@app.command()
def startstop():
    from community.app import settings
    from community.ingest.discord.utils.bot_client import BotClient

    client = BotClient()
    client.run(settings.DISCORD_BOT_TOKEN)


@app.command()
def stop():
    from community.ingest.discord.utils.bot_client import BotClient
    BotClient.kill_previous()


if __name__ == "__main__":
    app()
