import json

def force_dict_inner_list_ordering(payload: dict, *path: str) -> None:
    """
    Traverse `payload` following the path (e.g., ('fields','identifiers')).
    If the terminal value is a list, sort it deterministically in place.
    """
    if not path:
        return

    d = payload
    for key in path[:-1]:
        if not (isinstance(d, dict) and key in d):
            return  # path missing; nothing to do
        d = d[key]

    last = path[-1]
    if isinstance(d, dict) and last in d and isinstance(d[last], list):
        d[last].sort(key=lambda x: json.dumps(x, sort_keys=True))
