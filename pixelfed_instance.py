from pixelfed_python_api import Pixelfed


class PixelfedInstance:
    def __init__(self):
        pfi = Pixelfed().instance()

        if pfi is None:
            raise Exception("For some unknown reasons the Pixelfed instance returned empty values.")

        self._raw_data = pfi

    @property
    def get_max_characters(self):
        return self._raw_data['configuration']['statuses']['max_characters'] if self._raw_data \
            else None

    @property
    def get_max_media_attachments(self):
        return self._raw_data['configuration']['statuses']['max_media_attachments'] if \
            self._raw_data else None
