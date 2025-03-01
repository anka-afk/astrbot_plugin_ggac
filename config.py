import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

TEMP_DIR = os.path.join(CURRENT_DIR, os.pardir, os.pardir, "temp")
CACHE_DIR = os.path.join(CURRENT_DIR, os.pardir, os.pardir, "ggac_cache")
CARDS_DIR = os.path.join(TEMP_DIR, "cards")
FONTS_DIR = os.path.join(CURRENT_DIR, "GGAC_Scraper", "fonts", "微软雅黑.ttf")
