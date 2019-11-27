import utils
import subprocess
import random
import os

def test_byte_range_generation():
    # utils.get_byte_ranges is always passed in a number of threads less than equal to length bytes
    assert utils.get_byte_ranges(10, 3) == ["0-2", "3-5", "6-"]
    assert utils.get_byte_ranges(10, 1) == ["0-"]
    assert utils.get_byte_ranges(2, 2) == ["0-0", "1-"]


urls = [
    "http://cs241.cs.illinois.edu/images/favicons/uiuc.png",
    "https://one.walmart.com/content/dam/themepage/pdfs/AssociateBenefitsBook-2020.pdf",
    "http://humanstxt.org/humans.txt",
    "http://www.gilith.com/talks/ssv2010.pdf",
    "http://ia800304.us.archive.org/22/items/BuDrummonds_Bride/Bulldog_Drummonds_Bride_512kb.mp4",
]

def test_download():
    """
    End-to-end download test with a random number of threads.
    """
    # For reproducability
    random.seed(1)
    for url in urls:
        nThreads = random.randint(4, 9)

        filename = url.split("/")[-1]

        print(f"nThreads: {nThreads}")

        print(f"URL: {url}")

        # Run our downloader
        downloader_process = subprocess.run(["./downloader", url, "-c", f"{nThreads}"], capture_output=True)

        assert downloader_process.returncode == 0

        # Run wget
        wget_process = subprocess.run(["wget", url, "-O", f"wget_{filename}"], capture_output=True)

        assert wget_process.returncode == 0

        # diff both files
        diff_process = subprocess.run(["diff", filename, f"wget_{filename}"])

        # diff returns 0 when the files are exactly the same
        assert diff_process.returncode == 0

        os.unlink(filename)
        os.unlink(f"wget_{filename}")

