def chunkify(iterable, chunksize):
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= chunksize:
            yield chunk
            chunk = []
    if len(chunk) > 0:
        yield chunk
