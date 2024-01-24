import os
import sys
import requests
import random
import time
import cloudscraper
import subprocess
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tqdm import tqdm


def _download(download_folder, filename):
    print(f"\nDownloading image {i + 1}: {filename}")
    image_response = req_get(direct_image_link, stream=True)
    if image_response.status_code == 200:
        # Get the total file size to track progress
        total_size = int(image_response.headers.get('content-length', 0))

        # Save the image to the download folder with a progress bar
        with open(os.path.join(download_folder, filename), "wb") as image_file:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading image {i + 1}: {filename}", leave=False) as pbar:
                for data in image_response.iter_content(chunk_size=1024):
                    pbar.update(len(data))
                    image_file.write(data)

        print(f"\nDownloaded image {i + 1}: {filename}")
    else:
        print(image_response.text)
        print(f"Download failed for image {i + 1}: {filename}")

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
headers = {
        'User-Agent': UA,
        'Referer': 'https://bunkrr.su/',
        #'Host': 'bunkrr.su',
        #'User-Agent': 'curl/7.88.1',
}

scraper = cloudscraper.create_scraper()
def req_get(*args, **kw):
    for i in range(10):
        r = scraper.get(*args, headers=headers, **kw)
        if r.status_code == 200:
            return r
        else:
            time.sleep(random.random() * 5 * i)
    return r

# Gallery URL
if len(sys.argv) > 1:
    gallery_url = sys.argv[1]
else:
    gallery_url = input("Enter gallery URL: ")

print(gallery_url)
headers['Referer'] = gallery_url

# Send an HTTP GET request to the gallery URL
response = req_get(gallery_url)
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all anchor tags with href attributes
    # anchor_tags = soup.find_all("a", href=True)
    # Find all anchor tags with href attributes containing "/i/"
    anchor_tags = soup.find_all("a", href=lambda href: href and ("/i/" in href or "/v/" in href))
    print(f"Almost {len(anchor_tags)} files will be downloaded!")
    #input("Wanna continue?")

    # Create a folder to save the downloaded images
    slot = gallery_url.strip('/').split('/')[-1]
    download_folder = os.path.join("downloaded_images", slot)
    os.makedirs(download_folder, exist_ok=True)

    # Initialize a progress bar for downloading images
    progress_bar = tqdm(total=len(anchor_tags), unit="image")

    # Download the images linked in href attributes of anchor tags
    for i, anchor_tag in enumerate(anchor_tags):
        href = anchor_tag["href"]
        if "/i/" in href:  # Check if it's an image link
            image_page_url = f"https://bunkrr.su{href}"  # Construct the image page URL
            filename = href.replace('/i/', '')
            if os.path.exists(os.path.join(download_folder, filename)):
                print(f"\nFile exists: {filename}")
                progress_bar.update(1)  # Update the progress bar
                continue
            image_page_response = req_get(image_page_url)
            if image_page_response.status_code == 200:
                image_soup = BeautifulSoup(image_page_response.text, "html.parser")
                img_tags = image_soup.find_all("img", src=True)  # Find all img tags with src attribute
                img_tags += image_soup.find_all("source", src=True)  # Find all video tags with src attribute
                for img_tag in img_tags:
                    if "bunkr.ru" in img_tag["src"]:
                        direct_image_link = img_tag["src"]

                        # Extract the filename from the direct image link
                        filename = os.path.basename(urlparse(direct_image_link).path)

                        # Check if the file already exists in the download folder
                        if not os.path.exists(os.path.join(download_folder, filename)):
                            _download(download_folder, filename)
                        else:
                            print(f"\nFile exists: {filename}")

            progress_bar.update(1)  # Update the progress bar
        elif "/v/" in href:  # Check if it's an image link
            # # TODO(rlj): get video link from html.
            # direct_image_link = 'https://burger.bunkr.ru/{}'.format(href.strip('/').split('/')[-1])
            direct_image_link = 'https://taquito.bunkr.ru/{}'.format(href.strip('/').split('/')[-1])
            # Extract the filename from the direct image link
            filename = os.path.basename(urlparse(direct_image_link).path)

            # Check if the file already exists in the download folder
            if not os.path.exists(os.path.join(download_folder, filename)):
                #_download(download_folder, filename)
                subprocess.check_call([
                    'wget',
                    '-d',
                    f'--directory-prefix={download_folder}',
                    f'--header=User-Agent: {UA}',
                    '--header=Referer: https://bunkrr.ru/',
                    '--header=Range: bytes=0-',
                    direct_image_link,
                ])
            else:
                print(f"\nFile exists: {filename}")

            progress_bar.update(1)  # Update the progress bar
    progress_bar.close()  # Close the progress bar for downloading images

else:
    print(f"Failed to fetch the gallery page. Status code: {response.status_code}")
