#!/usr/bin/python3
import requests
import argparse
import concurrent.futures
import logging
import json
import sys
import time
import threading

import constants


def pprint(payload):
    """
    Pretty-prints dictionary-like objects.
    """
    logging.debug(json.dumps(dict(payload), indent=4, sort_keys=True))


def get_file_info(url):
    """
    If the given URL doesn't exist, this exits the program.
    Otherwise, returns a tuple with the length of the file, and a boolean indicating whether the file server supports partial requests respectively.
    """
    response = requests.head(url)

    pprint(response.headers)

    if response.status_code != requests.codes.ok:
        logging.critical("Bad URL passed in.")
        sys.exit(1)

    pprint(response.headers)

    ACCEPT_RANGES_HEADER = "Accept-Ranges"
    is_byte_range_supported = ACCEPT_RANGES_HEADER in response.headers and response.headers[
        ACCEPT_RANGES_HEADER] == "bytes"

    length = 0
    # We have to download this file in a single-threaded fashion if we cannot get the size
    if "Content-Length" not in response.headers:
        return 0, False
    else:
        return int(response.headers["Content-Length"]), is_byte_range_supported


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


def download_file_chunk(input):
    """
    Takes a filename, url, and byte range, and downloads a chunk of the file.
    """
    global lock
    filename = input['filename']
    url = input['url']
    file_range = input['range']
    starting_bytes = int(file_range.split("-")[0])
    written_bytes = 0

    logging.debug(f"My range is: {file_range}")

    with requests.get(url,
                      stream=True,
                      headers={"Range": f"bytes={file_range}"}) as stream:
        with lock: 
            with open(filename, "wb") as file:
                logging.debug(id(lock))
                for chunk in stream.iter_content(chunk_size=constants.CHUNK_SIZE):
                    file.seek(starting_bytes + written_bytes, 0)

                    file.write(chunk)

                    logging.debug(f"Chunk size: {len(chunk)}")

                    written_bytes += len(chunk)

        return written_bytes


def download_file_parallel(url, n_threads, filename, ranges):
    """
    This downloads the file in `n_threads` parts concurrently.
    Each part is chunked up as well, in case the part is also too large to fit into memory. 
    """
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=n_threads) as executor:
        inputs = [{
            'filename': filename,
            'url': url,
            'range': byte_range
        } for byte_range in ranges]

        logging.debug(json.dumps(list(inputs), indent=4, sort_keys=True))

        futures = executor.map(download_file_chunk, inputs)

        # Will contain the filenames of combined files
        return list(futures)


def download_file_single_threaded(url, filename):
    """
    Downloads a file using a single thread.
    """
    with requests.get(url, stream=True) as stream:
        with open(constants.DOWNLOAD_DIRECTORY + filename, "wb+") as file:
            for chunk in stream.iter_content(chunk_size=constants.CHUNK_SIZE):
                file.write(chunk)
        return filename

def serial_combine_parts(filenames):
    first_filename = filenames[0]
    with open(first_filename, "wb+") as combined_file:
        for filename in filenames[1:]:
            with open(filename) as partial:
                data = partial.read(constants.CHUNK_SIZE)


def combine_parts(filenames, method='serial'):
    if method=='serial':
        serial_combine_parts(filenames)
    elif method=='logtree':
        logtree_combine_parts(filenames)

def main():
    global lock
    lock = threading.Lock()

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s-%(relativeCreated)1d-%(threadName)s-%(message)s')

    logging.debug(id(lock))

    parser = argparse.ArgumentParser(
        description=
        'Download a file with nThreads number of threads. There will be a reasonable limit to the maximum value of this variable.'
    )
    parser.add_argument("url",
                        metavar="url",
                        type=str,
                        nargs=1,
                        action="store",
                        help="URL to file that will be downloaded")
    parser.add_argument('-c',
                        metavar='n_threads',
                        type=int,
                        nargs=1,
                        action="store",
                        required=True,
                        dest='n_threads',
                        help='an integer for the number of threads')

    # Steps
    # Check if file URL is valid
    # Get length of file
    # Use a function to break into ranges, based on n_threads
    # Cap nThreads to number of actual CPUs
    # Use a ThreadPoolExecutor to download files into file.[partOfRange]
    # Finally, combine pairs of successive parts into a single files
    # Rename to actual file's name (if we know it)

    arguments = vars(parser.parse_args())

    # To prevent servers from thinking this is a DDOS attack
    n_threads = min(constants.MAX_THREADS, arguments["n_threads"][0])

    logging.info(f"Number of threads: {n_threads}")

    url = arguments["url"][0]

    filename = url.split("/")[-1]

    length, is_byte_range_supported = get_file_info(url)

    logging.info(f"File size: {length}")

    start_time = None

    if is_byte_range_supported and n_threads > 1:

        logging.info(f"Downloading the file using {n_threads} threads.")
        ranges = get_byte_ranges(length, n_threads)

        logging.debug(f"Byte ranges: {ranges}")

        start_time = time.time()

        new_file = constants.DOWNLOAD_DIRECTORY + filename
        with open(new_file, 'wb+') as f:
            f.seek(length - 1, 0)
            f.write(b"\0")

        filenames = download_file_parallel(url, n_threads, new_file, ranges)

        # combine_parts(filenames)
    else:
        logging.info(
            f"Downloading file using a single thread."
        )

        start_time = time.time()

        download_file_single_threaded(url, filename)

    end_time = time.time()

    logging.info(
        f"File downloaded successfully in {end_time - start_time} seconds.")

    return 0

lock = None
if __name__ == "__main__":
    main()
