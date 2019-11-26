# Parallel File Downloader

## Installation
1. Clone this repository.
2. Get python3.6+.
3. Run `python3 -m virtualenv venv`.
4. Run the virtualenv activation script.
    - On Ubuntu, this is `source venv/bin/activate`
    - On Windows, you can run the bash script under `venv/bin`
5. Run `pip install -r requirements.txt` to fetch the external modules.
6. Set the relative download directory for all files in `constants.py`.
7. To learn how to use the program, run `./downloader.py -h`. For reference, usage is: `./downloader.py URL -c nThreads`.

## Assumptions
The intended behavior of the program is to download a file concurrently from an HTTP server, that ideally supports multi-part requests using byte-ranges. The file server must set the `Content-Length` in addition, to determine the size of the file prior to actually downloading it.

If either the file size cannot be determined using a `HEAD` HTTP request, or if the server does not support multi-part requests, the file will be downloaded serially.

## Design Choices
I am using Python's ThreadPoolExecutor that uses the multithreaded concurrency model to download roughly equally sized parts of the file concurrently (if possible). 

Even though Python has a Global Interpreter Lock (GIL) that forces threads to be interleaved on a single CPU as opposed to multiple cores, since file downloading is an I/O-heavy operation, this should still result in significant download time improvements relative to single-threaded downloading. 

Each part of the file is also streamed(a.k.a. "fetched in chunks") in the event that each part is too large to store in memory. We download a page at a time (4KiB), and store it to disk; this process continues until the entire chunk is downloaded.

Once the downloading completes, all the files are merged. This process is done in `O(log n)` time where `n` is the number of chunks of the file, as instead of merging serially, we merge consecutive blocks in parallel to minimize the on-disk I/O.

## Performance Bottlenecks

I have kept the maximum concurrent requests capped at 4, in order to prevent throttling from the server, and for this to be considered a denial-of-service attack. Most browsers have this limit set this to a number between 8 and 13 when fetching files.

If the number of threads is very high (possibly due to an unthinking user), the overhead incurred in switching between so many threads will lead to a slowdown.