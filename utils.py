import logging
import json

def get_byte_ranges(length, n_threads):
    """
    Given the length of a file and a number of threads, returns a list of inclusive byte ranges as strings.
    """
    # Because number of bytes is discrete
    range_size = length // n_threads
    ranges = []

    for i in range(n_threads - 1):
        ranges.append(f"{i * range_size}-{i * range_size + range_size - 1}")

    if len(ranges) >= 1:
        last_byte_range_start = int(ranges[-1].split("-")[1]) + 1
    else:
        last_byte_range_start = 0

    # Ensure we don't overextend our range
    ranges.append(f"{last_byte_range_start}-")
    return ranges

def pprint(payload):
    """
    Pretty-prints dictionary-like objects.
    """
    logging.debug(json.dumps(dict(payload), indent=4, sort_keys=True))
