from datetime import datetime


def parse_timestamp(s):
    if isinstance(s, int):
        return datetime.fromtimestamp(s)
    try:
        return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        dt_s, microseconds = s.split('.')
        new_s = '%s.%s' % (dt_s, microseconds[:6])
        try:
            return datetime.strptime(new_s, '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            return datetime.strptime(new_s, '%Y-%m-%dT%H:%M:%S.%fZ')
