from typing import List
import asyncio
from .ggac_scraper import (
    GGACScraper,
    CategoryType,
    MediaCategory,
    SortField,
    WorkItem,
)


class GGACAPI:
    """GGAC API接口类"""

    def __init__(self):
        self._scraper = GGACScraper()

    async def login(
        self,
        username: str,
        password: str,
    ) -> bool:
        """
        登录GGAC

        参数:
            username: 用户名
            password: 密码

        返回:
            bool: 登录是否成功
        """
        return await self._scraper.login(username, password)

    def login_sync(self, *args, **kwargs) -> bool:
        """同步方式登录GGAC"""
        return self._scraper.login_sync(*args, **kwargs)

    async def get_works(
        self,
        category: str = "featured",
        media_type: str = "2d",
        sort_by: str = "recommended",
        page: int = 1,
        size: int = 48,
    ) -> List[WorkItem]:
        """
        获取作品列表

        参数:
            category: 分类名称，可选值：
                     - "featured": 精选
                     - "game": 游戏
                     - "anime": 二次元
                     - "movie": 影视
                     - "art": 文创
                     - "comic": 动画漫画
                     - "other": 其他
                     - "all": 全部
                     - None: 不指定分类

            media_type: 创作类型，可选值：
                       - "2d": 2D原画
                       - "3d": 3D模型
                       - "ui": UI设计
                       - "animation": 动画
                       - "vfx": 特效
                       - "other": 其他
                       - None: 不指定创作类型

            sort_by: 排序方式，可选值：
                    - "latest": 最新
                    - "recommended": 推荐
                    - "views": 浏览量
                    - "likes": 点赞数
                    - "hot": 热度

            page: 页码，从1开始
            size: 每页数量，默认48

        返回:
            List[WorkItem]: 作品列表
        """
        # 转换分类
        category_map = {
            "featured": None,
            "game": CategoryType.GAME,
            "anime": CategoryType.ANIME,
            "movie": CategoryType.MOVIE,
            "art": CategoryType.ART,
            "comic": CategoryType.COMIC,
            "other": CategoryType.ANOTHER,
            "all": CategoryType.ALL,
        }

        # 转换创作类型
        media_type_map = {
            "2d": MediaCategory.TWO_D,
            "3d": MediaCategory.THREE_D,
            "ui": MediaCategory.UI,
            "animation": MediaCategory.ANIMATION,
            "vfx": MediaCategory.VFX,
            "other": MediaCategory.OTHER,
        }

        # 转换排序方式
        sort_map = {
            "latest": SortField.LATEST,
            "recommended": SortField.RECOMMENDED,
            "views": SortField.VIEWS,
            "likes": SortField.LIKES,
            "hot": SortField.HOT,
        }

        # 获取枚举值
        category_type = category_map.get(category.lower()) if category else None
        media_category = media_type_map.get(media_type.lower()) if media_type else None
        sort_field = sort_map.get(sort_by.lower(), SortField.RECOMMENDED)

        # 获取作品
        if category == "featured":
            return await self._scraper.get_featured_works(
                page=page,
                size=size,
                sort_field=sort_field,
                media_category=media_category,
            )
        else:
            return await self._scraper.get_works_by_category(
                category=category_type,
                page=page,
                size=size,
                sort_field=sort_field,
                media_category=media_category,
            )

    def get_works_sync(self, *args, **kwargs) -> List[WorkItem]:
        """同步方式获取作品列表"""
        return asyncio.run(self.get_works(*args, **kwargs))
