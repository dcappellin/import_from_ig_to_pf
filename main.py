import json
import os.path
import click

from pixelfed_instance import PixelfedInstance

from pixelfed_python_api import Pixelfed

IG_POSTS_FILE_PATH = os.path.join('content', 'posts_1.json')
IG_POSTS_MEDIA_PATH = os.path.join('media', 'posts')


def add_image_to_pixelfed(media_path, dry_run):
    if dry_run:
        return None

    resp = Pixelfed().media(media_path)
    print(resp)
    return resp['id']


def create_post_with_uploaded_media(status, added_media_ids, visibility, dry_run):
    if dry_run:
        return None

    Pixelfed().statuses(status=status, media_ids=added_media_ids, visibility=visibility)


@click.command()
@click.option('--ig-exported-path', type=click.Path(exists=True))
@click.option('--visibility',
              type=click.Choice(['unlisted', 'public', 'private']),
              required=True,
              default='unlisted',
              show_default=True)
@click.option('--custom_tag', help="Add a custom hashtag at the end of"
                                   "every imported post caption.")
@click.option('--dry-run', is_flag=True)
@click.option('--verbose', is_flag=True)
def import_to_pixelfed(ig_exported_path, dry_run, custom_tag, visibility, verbose):
    pfi = PixelfedInstance()

    if not is_ig_folder_valid(ig_exported_path):
        exit(-1)

    with open(os.path.join(ig_exported_path, IG_POSTS_FILE_PATH), encoding='raw-unicode-escape') \
            as file:
        posts = json.loads(file.read().encode('raw_unicode_escape').decode())
    print(f"Found {len(posts)} posts to import.")

    for post in posts:
        added_media_ids = []
        for media in post['media']:
            media_path = os.path.join(ig_exported_path, media['uri'])
            if os.path.isfile(media_path):
                print('> Image exists') if verbose else ''
                added_media_ids.append(add_image_to_pixelfed(media_path, dry_run))

        # TODO create more posts if medias are more than server limit
        if len(added_media_ids) > pfi.get_max_media_attachments:
            print(f'Skipped. {len(added_media_ids)} medias, but server supports only '
                  f'{pfi.get_max_media_attachments} per status.')
            continue

        if len(post['media']) == 1:
            status_title = f'{media["title"]} {custom_tag}' if custom_tag else media["title"]
        else:
            status_title = f'{post["title"]} {custom_tag}' if custom_tag else post["title"]

        # TODO find a way to publish long post
        if len(status_title) > pfi.get_max_characters:
            print(f'Skipped. Status caption is {len(status_title)} chars, but server supports '
                  f'only {pfi.get_max_characters} chars per status.')

        resp = create_post_with_uploaded_media(status_title, added_media_ids, visibility, dry_run)
        print(resp)

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