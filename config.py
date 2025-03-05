import os
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

TEMP_DIR = os.path.join(CURRENT_DIR, os.pardir, os.pardir, "temp")
CACHE_DIR = os.path.join(CURRENT_DIR, os.pardir, os.pardir, "ggac_cache")
CARDS_DIR = os.path.join(TEMP_DIR, "cards")
FONTS_DIR = os.path.join(CURRENT_DIR, "GGAC_Scraper", "fonts", "ChillRoundM.ttf")
SETTINGS_DIR = os.path.join(CACHE_DIR, "settings.json")

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

MEDIA_TYPE_MAP = {
    "全部": None,
    "2D原画": 1,
    "3D模型": 2,
    "动画": 3,
    "视频": 4,
    "摄影": 5,
    "其他": 6,
    "文章": 8,
}

# 默认推送设置
DEFAULT_SETTINGS = {
    "精选2D": {"category": "精选", "media_type": "2D原画", "sort_by": "推荐"},
    "热门3D": {"category": "精选", "media_type": "3D模型", "sort_by": "热度"},
}


def init_settings():
    """初始化设置文件"""
    os.makedirs(os.path.dirname(SETTINGS_DIR), exist_ok=True)

    if not os.path.exists(SETTINGS_DIR):
        with open(SETTINGS_DIR, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=2)
        print(f"已创建默认设置文件: {SETTINGS_DIR}")


def load_settings():
    """加载设置文件"""
    try:
        with open(SETTINGS_DIR, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"设置文件不存在，将创建默认设置")
        init_settings()
        return DEFAULT_SETTINGS
    except json.JSONDecodeError:
        print(f"设置文件格式错误，将使用默认设置")
        return DEFAULT_SETTINGS


def save_settings(settings):
    """保存设置文件"""
    with open(SETTINGS_DIR, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


init_settings()
