# Data is streamed in CHUNK_SIZE bytes sized chunks. It is recommended to set this to be a multiple of page size (often 4kB)
CHUNK_SIZE = 4096

# Max number of worker threads used, regardless of command-line arguments to program
MAX_THREADS = 8

# Directory where the files are downloaded
DOWNLOAD_DIRECTORY = "./"

# Max retries if the connection is dropped
MAX_RETRIES = 5