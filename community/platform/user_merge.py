from collections import defaultdict


def merge(users):
    groups = defaultdict(list)
    for d in users:
        groups[d['name']].append(d)

    with_final = []
    for k, g in groups.items():
        final_user = min(g, key=lambda x: x['id'])
        others = [u for u in g if u != final_user]
        with_final.append((final_user, others))

    return with_final
