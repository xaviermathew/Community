from tqdm import tqdm
import typer


def main():
    from community.ingest.github.models import GithubRepo

    qs = GithubRepo.filter().all()
    for obj in tqdm(qs):
        obj.crawl_messages()


if __name__ == "__main__":
    typer.run(main)
