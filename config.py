import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

TEMP_DIR = os.path.join(CURRENT_DIR, os.pardir, os.pardir, "temp")
CACHE_DIR = os.path.join(CURRENT_DIR, os.pardir, os.pardir, "ggac_cache")
CARDS_DIR = os.path.join(TEMP_DIR, "cards")
FONTS_DIR = os.path.join(CURRENT_DIR, "GGAC_Scraper", "fonts", "微软雅黑.ttf")

# 转换设置文件中的中英文映射, 例如 2D原画->2d
CATEGORY_MAP = {
    "2D原画": "2d",
    "3D模型": "3d",
    "UI设计": "ui",
    "动画": "animation",
    "特效": "vfx",
    "其他": "other",
    "不指定创作类型": "None",
    "精选": "featured",
    "游戏": "game",
    "二次元": "anime",
    "影视": "movie",
    "文创": "art",
    "动画漫画": "comic",
    "其他": "other",
    "全部": "all",
    "不指定分类": "None",
    "最新": "latest",
    "推荐": "recommended",
    "浏览量": "views",
    "点赞": "likes",
    "热度": "hot",
}
