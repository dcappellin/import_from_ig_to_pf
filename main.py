import json
import math
import os.path
import textwrap
import time
from pathlib import Path

import click

from pixelfed_instance import PixelfedInstance

from pixelfed_python_api import Pixelfed

IG_POSTS_FILE_PATH = os.path.join('content', 'posts_1.json')
IG_POSTS_MEDIA_PATH = os.path.join('media', 'posts')


def add_image_to_pixelfed(media_path, dry_run, verbose):
    print(f'Posting media {media_path}...')
    media_id = None
    if not dry_run:
        resp = Pixelfed().media(media_path)
        if verbose:
            print(json.dumps(resp, indent=4))
        media_id = resp['id']
    print('...done.')

    return media_id


def create_status_with_uploaded_media(status, added_media_ids, visibility, dry_run, verbose):
    print('Posting status...')
    if not dry_run:
        resp = Pixelfed().statuses(status=status, media_ids=added_media_ids, visibility=visibility)
        if verbose:
            print(json.dumps(resp, indent=4))
    print('...done.')


@click.command()
@click.option('--ig-exported-path', type=click.Path(exists=True))
@click.option('--visibility',
              type=click.Choice(['unlisted', 'public', 'private']),
              required=True,
              default='unlisted',
              show_default=True)
@click.option('--custom-hashtag', help="Add a custom hashtag at the end of"
                                       "every imported post caption.")
@click.option('--dry-run', is_flag=True)
@click.option('--verbose', is_flag=True)
def import_to_pixelfed(ig_exported_path, dry_run, custom_hashtag, visibility, verbose):
    if dry_run:
        print('dry-run is enable. Nothing will be posted to Pixelfed.')

    pfi = PixelfedInstance()

    if not is_ig_folder_valid(ig_exported_path):
        exit(-1)

    with open(os.path.join(ig_exported_path, IG_POSTS_FILE_PATH), encoding='raw-unicode-escape') \
            as file:
        posts = json.loads(file.read().encode('raw_unicode_escape').decode())
    print(f"Found {len(posts)} posts to import.")

    for post in posts:

        parts = math.ceil(len(post['media']) / pfi.get_max_media_attachments)
        for part in range(parts):
            status_title = ''
            if parts > 1:
                status_title = f'{part + 1}/{parts} '

            status_max_characters = pfi.get_max_characters - (len(custom_hashtag) if custom_hashtag else 0) - len(status_title) - 2
            if len(post['media']) == 1:
                status_title += textwrap.shorten(f'{post["media"][0]["title"]}',
                                                 status_max_characters)
            else:
                status_title += textwrap.shorten(f'{post["title"]}', status_max_characters)
            if custom_hashtag:
                status_title += f' #{custom_hashtag}'
            if verbose:
                print(f"> Status({len(status_title)} chars): {status_title}")

            if len(status_title) > pfi.get_max_characters:
                print(f'Skipped. Status caption is {len(status_title)} chars, but server supports '
                      f'only {pfi.get_max_characters} chars per status.')
                continue

            start = part * pfi.get_max_media_attachments
            stop = min((part + 1) * pfi.get_max_media_attachments, len(post['media']))

            added_media_ids = []
            for media_index in range(start, stop):
                if verbose:
                    print(f"> Media n.{media_index}")
                media = post['media'][media_index]
                media_path = os.path.join(ig_exported_path, media['uri'])
                if os.path.isfile(media_path) and Path(media_path).suffix.lower() == '.jpg':
                    print('> Image exists') if verbose else ''
                    added_media_ids.append(add_image_to_pixelfed(media_path, dry_run, verbose))
                    time.sleep(1)

            if len(added_media_ids) >= 1:
                create_status_with_uploaded_media(status_title, added_media_ids, visibility, dry_run, verbose)
                time.sleep(1)

    print("Import completed.")


def is_ig_folder_valid(ig_exported_path) -> bool:
    if not os.path.isdir(os.path.join(ig_exported_path, IG_POSTS_MEDIA_PATH)):
        print(f"Missing {IG_POSTS_MEDIA_PATH} folder in {ig_exported_path}.")
        return False

    if not os.path.isfile(os.path.join(ig_exported_path, IG_POSTS_FILE_PATH)):
        print(f"Missing {IG_POSTS_FILE_PATH} file in {ig_exported_path}")
        return False

    return True


if __name__ == '__main__':
    import_to_pixelfed()
