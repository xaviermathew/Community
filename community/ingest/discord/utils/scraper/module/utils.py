from datetime import datetime

DEFAULT_CONFIG = {
    "useragent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.309 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36",
    "buffer": 1048576,
    "options": {
        "validateFileHeaders": False,
        "generateFileChecksums": False,
        "sanitizeFileNames": True,
        "compressImageData": False,
        "compressTextData": False,
        "gatherJSONData": True
    },
    "query": {
        "images": False,
        "files": False,
        "embeds": False,
        "links": False,
        "videos": False,
        "nsfw": True
    },
    "types": {
        "images": True,
        "videos": True,
        "files": True,
        "text": True
    },
    "directs": {
    },
    "guilds": {}
}


def parse_timestamp(s):
    if isinstance(s, int):
        return datetime.fromtimestamp(s)

    dt_s, tz_s = s.split('+')
    new_dt_s = dt_s + '+' + tz_s.replace(':', '')
    try:
        return datetime.strptime(new_dt_s, '%Y-%m-%dT%H:%M:%S.%f%z')
    except ValueError:
        return datetime.strptime(new_dt_s, '%Y-%m-%dT%H:%M:%S%z')
