from client import get_localization


class Localization:
    def __init__(self, language=None):
        self.localization = {}
        if language:
            self.reload(language)

    def __call__(self, key):
        return self.localization.get(key, key)

    def reload(self, language):
        get_localization(language=language, on_success=self.set_localization, on_failure=print)

    def set_localization(self, localization):
        self.localization = localization


localization = Localization()
