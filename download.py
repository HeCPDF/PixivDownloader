import requests
import time
import mimetypes
import signal
import concurrent.futures
import sys
import os

addr : str = "https://pixiv.cat"

MAX_RETRIES = 16
MAX_WORKERS = 256
FILENAME_EXTENSION = "png"

try:
    os.mkdir('downloaded')
except FileExistsError:
    pass

skipped_urls = []

def signal_handler(sig, frame):
    print("\nSkipped URLs:")
    for url in skipped_urls:
        print(url)
    print("\nCanceled by User")
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

def downloadFile(params):
    num1, num2 = params
    url = f"{addr}/{num1}.{FILENAME_EXTENSION}" if num2 == 0 else f"{addr}/{num1}-{num2}.{FILENAME_EXTENSION}"

    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(url)
            if response.status_code == 404:
                break
            elif response.status_code == 503:
                break
            elif response.status_code == 200:
                break
            else:
                print(f"Non-404or503or200 code: {response.status_code}, retrying...")
        except Exception as e:
            print(f"Exception occurred: {e}")
        time.sleep(5)
        retries += 1
    else:
        print(f"Skipping URL after {MAX_RETRIES} failed attempts: {url}")
        skipped_urls.append(url)
        return

    if response.text.startswith("<!DOCTYPE html>"):
        if response.status_code == 404:
            pass
        elif response.status_code == 503:
            pass
        elif response.status_code == 200:
            print(f"API rate limited. Wait 60 sec...")
            time.sleep(60)
            downloadFile((num1, 0 if num2 == 0 else num2))
    else:
        filename = f"{num1}" if num2 == 0 else f"{num1}-{num2}"
        ext = mimetypes.guess_extension(response.headers['content-type'])
        with open('downloaded/' + filename + ext, 'wb') as f:
            f.write(response.content)
        if num2 == 0:
            print(f"{num1} saved")
        else:
            print(f"{num1}-{num2} saved")

start = int(sys.argv[1])
end = int(sys.argv[2])
print(start,end)
i = start
task_counter = 0

while True:
    if end != -1 and i > end:
        print(f"Finished the Task!")
        break

    params = []

    url = f"{addr}/{i}.{FILENAME_EXTENSION}"
    response = requests.get(url)

    if response.status_code != 404 and response.history and "Location" in response.history[0].headers and f"{i}-1.{FILENAME_EXTENSION}" in response.history[0].headers["Location"]:
        for j in range(1, 128):
            params.append((i, j))
    else:
        params.append((i, 0))

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(downloadFile, params)
    
    i += 1
    task_counter += len(params)