from tqdm import tqdm
import typer


def main():
    from community.ingest.discord.models import DiscordGuild

    dg_set = DiscordGuild.filter().all()
    for dg in tqdm(dg_set):
        dg.crawl_messages()


if __name__ == "__main__":
    typer.run(main)
