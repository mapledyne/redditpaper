import os
import praw
import sys
import pickle
import pwd
import requests
import logging

from urllib.parse import urlparse

config = {}

config['REDDITPAPER_NAME'] = os.environ.get("REDDITPAPER_NAME")
config['REDDITPAPER_ID'] = os.environ.get("REDDITPAPER_ID")
config['REDDITPAPER_SECRET'] = os.environ.get("REDDITPAPER_SECRET")
config['REDDIT_USER'] = os.environ.get("REDDIT_USER")
config['REDDIT_PASS'] = os.environ.get("REDDIT_PASS")
config['REDDITPAPER_SUB'] = os.environ.get("REDDITPAPER_SUB", "wallpapers")

for item in config:
    if config[item] is None:
        print(f"ERROR: {item} is not set. Please set this env variable and retry.")
        sys.exit(1)


def wallpaper_directory():
    username = pwd.getpwuid(os.getuid()).pw_name
    directory = "/Users/" + username + "/Pictures/Wallpapers/"
    return directory


def load_scraped():
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
    print(f"Saving: {file}")
    open(file, 'wb').write(r.content)


if __name__ == "__main__":
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
