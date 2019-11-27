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
7. To learn how to use the program, run `./downloader -h`. For reference, usage is: `./downloader.py URL -c nThreads`.

## Assumptions
The intended behavior of the program is to download a file concurrently from an HTTP server, that ideally supports multi-part requests using byte-ranges. The file server must set the `Content-Length` in addition, to determine the size of the file prior to actually downloading it.

If either the file size cannot be determined using a `HEAD` HTTP request, or if the server does not support multi-part requests, the file will be downloaded serially.

## Design Choices
I am using Python's ThreadPoolExecutor that uses the multithreaded concurrency model to download roughly equally sized parts of the file concurrently (if possible). 

Even though Python has a Global Interpreter Lock (GIL) that forces threads to be interleaved on a single CPU as opposed to multiple cores, since file downloading is an I/O-heavy operation, this should still result in significant download time improvements relative to single-threaded downloading, as most of the time is spent waiting for data to arrive through the network. 

Each part of the file is also streamed(a.k.a. "fetched in chunks") in the event that each part is too large to store in memory. We download a page at a time (4KiB), and store it to disk; this process continues until the entire chunk is downloaded.

Once the downloading completes, all the files are merged. This is done by appending each file after the first to the first file.

This merging process can be optimized, but I decided not to implement it, assuming that bottleneck on a server is not disk speed but network bandwidth.

## Performance Bottlenecks

I have kept the maximum concurrent requests capped at 4, in order to prevent throttling from the server, and for this to be considered a denial-of-service attack. Most browsers have this limit set this to a number between 8 and 13 when fetching files.

If the number of threads is very high (possibly due to an unthinking user), the overhead incurred in switching between so many threads will lead to a slowdown.

## Potential Improvements / Optimizations

- The file merging process can be done in `O(log n)` time where `n` is the number of chunks of the file, as instead of merging serially, we merge consecutive blocks in parallel to minimize the on-disk I/O.

- If this downloader is used multiple times, we can cache files that are downloaded multiple times, by keeping track of downloaded files in a persistent store (e.g. SQL database).

- It would be nice if this downloader could support pause / resume semantics, similar to how deep learning packages can resume model training by reading past weights from a file. 

- If the downloading of multiple files needs to be supported, it probably makes sense to parallelize the download of each file, as opposed to chunks of files. This tool could support a configuration file / job description language which is parsed to process a list of files, and options for how they should be downloaded, including priority levels.

- This tool could be designed to support other protocols such as SSH and FTP.