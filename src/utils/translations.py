import os
import json
import src.utils.settings as settings
import logging

class Translator:
    def __init__(self, language="en-US"):
        self.language = language
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        try:
            with open(os.path.join('src', 'i18n', f"{self.language}.json"), "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            logging.error(f"No translation file found for language: {self.language}. Using default English.")
    
    def translate(self, cog, key):
        keys = key.split('.')
        value = self.translations.get(cog, {})
        for k in keys:
            value = value.get(k, None)
            if value is None:
                return f"{cog}.{key}"
        return value

    def set_language(self, language):
        self.language = language
        self.load_translations()

translator = Translator(settings.bot_language)

def t(cog, key):
    return translator.translate(cog, key)
