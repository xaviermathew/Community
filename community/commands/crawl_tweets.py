from tqdm import tqdm
import typer


def main():
    from community.ingest.twitter.models import TwitterHandle

    th_set = TwitterHandle.filter().all()
    for th in tqdm(th_set):
        th.crawl_messages()


if __name__ == "__main__":
    typer.run(main)
