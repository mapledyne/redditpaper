"""
A simple script to download images from Reddit
for use as wallpapers.

Run this as a cron job to pull new images over time - this script caches images
that have been downloaded so only new images will be grabbed.

Pair this with tmpwatch to delete old images and you always have fresh
backgrounds.

Note: It currently is Mac only.
"""
import logging
import os
import pickle
import praw
import pwd
import requests
import sys

from urllib.parse import urlparse

config = {}

config['REDDITPAPER_NAME'] = os.environ.get("REDDITPAPER_NAME")
config['REDDITPAPER_ID'] = os.environ.get("REDDITPAPER_ID")
config['REDDITPAPER_SECRET'] = os.environ.get("REDDITPAPER_SECRET")
config['REDDIT_USER'] = os.environ.get("REDDIT_USER")
config['REDDIT_PASS'] = os.environ.get("REDDIT_PASS")
config['REDDITPAPER_SUB'] = os.environ.get("REDDITPAPER_SUB", "wallpapers")
config['REDDITPAPER_MAXSAVE'] = int(os.environ.get("REDDITPAPER_MAXSAVE", "5"))

def wallpaper_directory():
    """Return the wallpaper directory to save to."""
    username = pwd.getpwuid(os.getuid()).pw_name
    directory = "/Users/" + username + "/Pictures/Wallpapers/"
    return directory


def load_scraped():
    """Pull the cache of already downloaded images."""
    try:
        with open('scraped_files', 'rb') as fp:
            itemlist = pickle.load(fp)
            return itemlist
    except FileNotFoundError:
        return []


def save_scraped(scraped):
    with open('scraped_files', 'wb') as fp:
        pickle.dump(scraped, fp)


def save_image(url, filename):
    logging.info(f"Saving image {filename} from url {url}")
    r = requests.get(url, allow_redirects=True)
    file = wallpaper_directory() + filename
    logging.info(f"Saving: {file}")
    open(file, 'wb').write(r.content)


if __name__ == "__main__":

    # Simple sanity check for config values.
    for item in config:
        if config[item] is None:
            logging.error(f"ERROR: {item} is not set. Please set this env variable and retry.")
            sys.exit(1)

    reddit = praw.Reddit(client_id=config['REDDITPAPER_ID'],
                         client_secret=config['REDDITPAPER_SECRET'],
                         user_agent=config['REDDITPAPER_NAME'],
                         username=config['REDDIT_USER'],
                         password=config['REDDIT_PASS'])

    scraped = load_scraped()
    wallpaper = reddit.subreddit(config['REDDITPAPER_SUB'])

    topwalls = wallpaper.top(time_filter='week', limit=20)

    count = 0
    for wall in topwalls:
        filename = os.path.basename(urlparse(wall.url).path)

        if not filename.endswith('jpg') and not filename.endswith('png'):
            logging.info(f"{wall.title} : Wallpaper not an image.")
            continue
        if wall.over_18:
            logging.info(f"{wall.title} : Wallpaper NSFW.")
            continue
        if wall.id in scraped:
            logging.info(f'{wall.title} : This wallpaper has already been scraped')
            continue
        logging.info(f"{wall.title} : Wallpaper good to download.")
        scraped.append(wall.id)
        count += 1
        save_image(wall.url, filename)
        # only save five wallpapers per run:
        if count == 5:
            break

    save_scraped(scraped)
