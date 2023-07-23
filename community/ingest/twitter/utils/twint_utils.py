import datetime
import logging
import string

from retry import retry
import twint

from community.platform.utils.file_utils import mkdirs

_LOG = logging.getLogger(__name__)
PUNCT = set(string.punctuation)
PUNCT.add(' ')


def slugify(s, joiner='_', retain_punct=None):
    if retain_punct is None:
        retain_punct = set()
    result = []
    for c in s.lower():
        if c in PUNCT and c not in retain_punct:
            result.append(joiner)
        else:
            result.append(c)
    return joiner.join(filter(bool, ''.join(result).split(joiner)))


class CrawlBuffer(object):
    CRAWL_TYPE_TWEETS = 0
    CRAWL_TYPE_MENTIONS = 1
    CRAWL_TYPE_REPLIES = 2
    CRAWL_TYPE_HASHTAG = 3

    HANDLE_CRAWL_TYPES = (
        CRAWL_TYPE_TWEETS,
        CRAWL_TYPE_MENTIONS,
        CRAWL_TYPE_REPLIES
    )

    def __init__(self, job, crawl_type, limit=None, since=None, until=None,
                 language=None, buffer_size=25 * 1000):
        c = twint.Config()
        if crawl_type == self.CRAWL_TYPE_TWEETS:
            c.Username = job.query
        elif crawl_type in (self.CRAWL_TYPE_MENTIONS, self.CRAWL_TYPE_REPLIES):
            c.Search = '@' + job.query
        elif crawl_type == self.CRAWL_TYPE_HASHTAG:
            c.Search = '#' + job.query
        else:
            c.Search = job.query

        if since:
            c.Since = since

        if until:
            c.Until = until

        if limit:
            c.Limit = limit

        if language:
            c.Lang = language

        c.Store_object = True
        c.Store_object_tweets_list = self

        self.twint_config = c
        self.job = job
        self.signature_parts = map(str, [job.query, job.crawl_type, job.id])

        c.Resume = self.resume_fname

        self.buffer = []
        self.buffer_size = buffer_size

    @property
    def resume_fname(self):
        mkdirs('state/twint/')
        prefix = 'state/twint/resume_%s.txt'
        s = slugify('_'.join(self.signature_parts), retain_punct={'@'})
        return prefix % s

    def flush(self):
        from community.ingest.twitter.models import Tweet

        _LOG.info('flushing buffer for [%s]', self.signature_parts)
        objs = []
        for d in self.buffer:
            objs.append(Tweet(job=self.job,
                              id=d['id'],
                              message=d['tweet'],
                              timestamp=datetime.datetime.strptime(d['datetime'], '%Y-%m-%d %H:%M:%S %Z'),
                              user_id=d['user_id'],
                              data=d))
        Tweet.bulk_create(objs)
        self.buffer = []

    def append(self, tweet):
        self.buffer.append(vars(tweet))
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def close(self):
        if self.buffer:
            self.flush()

    @retry(tries=1000)
    def start_crawl(self):
        twint.run.Search(self.twint_config)
        self.close()
