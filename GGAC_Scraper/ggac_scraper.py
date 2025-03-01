from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
import aiohttp
import asyncio
from datetime import datetime


class SortField(str, Enum):
    """排序方式枚举"""

    LATEST = "lastSubmitTime"  # 最新
    RECOMMENDED = "recommendUpdateTime"  # 推荐
    VIEWS = "viewCount"  # 浏览
    LIKES = "likeCount"  # 点赞
    HOT = "threeDaysHot"  # 热度

    def __str__(self):
        return self.value


class CategoryType(str, Enum):
    """分类类型枚举"""

    FEATURED = 10000  # 精选
    ALL = 1000  # 全部
    GAME = 1  # 游戏
    ANIME = 2  # 二次元
    MOVIE = 3  # 影视
    ART = 4  # 文创,潮流,艺术
    COMIC = 5  # 动画漫画
    ANOTHER = 17  # 其他


class MediaCategory(str, Enum):
    """创作类型枚举"""

    TWO_D = 1  # 2D原画
    THREE_D = 2  # 3D模型
    UI = 4  # UI设计
    ANIMATION = 5  # ANI动画
    OTHER = 6  # 其他
    VFX = 7  # VFX特效


class RequestError(Exception):
    """请求错误"""

    pass


@dataclass
class Category:
    """分类信息"""

    id: int
    level: int
    name: str
    code: str


@dataclass
class WorkItem:
    """作品数据模型"""

    id: int
    title: str
    cover_url: str
    media_category: str
    username: str
    categories: List[Category]
    view_count: int
    hot: int
    create_time: datetime
    url: str

    @classmethod
    def from_dict(cls, data: dict) -> "WorkItem":
        """从API响应数据创建WorkItem实例"""
        work_id = data["id"]

        try:
            media_category = data["dictMap"]["mediaCategory"]
        except (KeyError, TypeError):
            media_category = "2D原画"
            print(
                f"Warning: Missing mediaCategory for work {work_id}, using default value"
            )

        return cls(
            id=work_id,
            title=data["title"],
            cover_url=data["originalCoverUrl"],
            media_category=media_category,
            username=data["userInfo"]["username"],
            categories=[
                Category(
                    id=cat["id"], level=cat["level"], name=cat["name"], code=cat["code"]
                )
                for cat in data["categoryList"]
            ],
            view_count=data["viewCount"],
            hot=data.get("hot", 0),
            create_time=datetime.strptime(data["createTime"], "%Y-%m-%d %H:%M:%S"),
            url=f"https://www.ggac.com/work/detail/{work_id}",
        )


@dataclass
class ArticleItem:
    """文章数据模型"""

    id: int
    title: str
    cover_url: str
    username: str
    categories: List[Category]
    view_count: int
    hot: int
    create_time: datetime
    url: str

    @classmethod
    def from_dict(cls, data: dict) -> "ArticleItem":
        """从API响应数据创建ArticleItem实例"""
        article_id = data["dataId"]
        return cls(
            id=article_id,
            title=data["title"],
            cover_url=data["coverUrl"],
            username=data["userInfo"]["username"],
            categories=[
                Category(
                    id=cat["id"], level=cat["level"], name=cat["name"], code=cat["code"]
                )
                for cat in data.get("categoryList", [])
            ],
            view_count=data["viewCount"],
            hot=data.get("hot", 0),
            create_time=datetime.strptime(data["createTime"], "%Y-%m-%d %H:%M:%S"),
            url=f"https://www.ggac.com/article/detail/{article_id}",
        )


@dataclass
class BaseScraper:
    """基础爬虫类"""

    pageNumber: int = 1
    pageSize: int = 48
    sort_field: SortField = SortField.RECOMMENDED
    media_category: Optional[MediaCategory] = None
    base_url: str = "https://www.ggac.com/api"
    max_retries: int = 3
    retry_delay: float = 1.0

    async def fetch_with_retry(self, url: str) -> dict:
        """带重试的请求方法"""
        print(f"\n[DEBUG] Requesting URL: {url}")

        async with aiohttp.ClientSession() as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.get(url, ssl=False) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"[DEBUG] Response status: {response.status}")
                            print(
                                f"[DEBUG] Response data preview: {str(data)[:200]}..."
                            )
                            return data
                        raise RequestError(
                            f"HTTP {response.status}: {await response.text()}"
                        )
                except Exception as e:
                    print(f"[DEBUG] Request attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def fetch_data(self) -> dict:
        """获取数据"""
        url = self._build_url()
        return await self.fetch_with_retry(url)

    def _build_url(self) -> str:
        """构建基础URL"""
        url = f"{self.base_url}/work/list?pageNumber={self.pageNumber}&pageSize={self.pageSize}&isPublic=1"
        if self.media_category:
            url += f"&mediaCategory={self.media_category.value}"
        print(f"[DEBUG] Built URL: {url}")
        return url

    @staticmethod
    def parse_response(response: dict) -> List[dict]:
        """解析响应数据"""
        print(f"[DEBUG] Response code: {response.get('code')}")
        print(f"[DEBUG] Response message: {response.get('message')}")

        if response.get("code") != "0":
            raise Exception(f"请求失败: {response.get('message')}")

        page_data = response.get("data", {}).get("pageData", [])
        print(f"[DEBUG] Found {len(page_data)} items in response")
        return page_data

    async def get_works(self, page: int = 1, size: int = 48) -> List[WorkItem]:
        """获取作品列表"""
        self.pageNumber = page
        self.pageSize = size
        response = await self.fetch_data()
        data = self.parse_response(response)
        return [WorkItem.from_dict(item) for item in data]


class FeaturedScraper(BaseScraper):
    """精选爬虫"""

    def __init__(
        self,
        page_number: int = 1,
        page_size: int = 48,
        sort_field: SortField = SortField.RECOMMENDED,
        media_category: Optional[MediaCategory] = None,
    ):
        super().__init__(
            pageNumber=page_number,
            pageSize=page_size,
            sort_field=sort_field,
            media_category=media_category,
        )

    def _build_url(self) -> str:
        """构建精选页面的URL"""
        url = (
            f"{self.base_url}/work/list"
            f"?pageNumber={self.pageNumber}"
            f"&pageSize={self.pageSize}"
            f"&isPublic=1"
            f"&isRecommend=1"
            f"&sortField={str(self.sort_field)}"
        )
        if self.media_category:
            url += f"&mediaCategory={self.media_category.value}"
        print(f"[DEBUG] Built Featured URL: {url}")
        return url


class CategoryScraper(BaseScraper):
    """分类爬虫"""

    def __init__(
        self,
        category: CategoryType,
        page_number: int = 1,
        page_size: int = 48,
        sort_field: SortField = SortField.RECOMMENDED,
        media_category: Optional[MediaCategory] = None,
    ):
        super().__init__(
            pageNumber=page_number,
            pageSize=page_size,
            sort_field=sort_field,
            media_category=media_category,
        )
        self.category = category

    def _build_url(self) -> str:
        """构建分类页面的URL"""
        url = super()._build_url()
        if self.category != CategoryType.ALL:
            url += f"&categoryId={self.category}"
        url += f"&sortField={str(self.sort_field)}"
        return url


class ArticleScraper(BaseScraper):
    """文章爬虫"""

    def __init__(
        self,
        page_number: int = 1,
        page_size: int = 48,
        sort_field: SortField = SortField.RECOMMENDED,
    ):
        super().__init__(
            pageNumber=page_number,
            pageSize=page_size,
            sort_field=sort_field,
        )

    def _build_url(self) -> str:
        """构建文章页面的URL"""
        return f"{self.base_url}/global_search/post?pageNumber={self.pageNumber}&pageSize={self.pageSize}&dataTable=article&sortField={self.sort_field}"

    async def get_articles(self) -> List[ArticleItem]:
        """获取文章列表"""
        response = await self.fetch_data()
        data = self.parse_response(response)
        return [ArticleItem.from_dict(item) for item in data]


class GGACScraper:
    """GGAC爬虫管理类"""

    def __init__(self):
        self.featured = FeaturedScraper()
        self.game = CategoryScraper(CategoryType.GAME)
        self.anime = CategoryScraper(CategoryType.ANIME)
        self.movie = CategoryScraper(CategoryType.MOVIE)
        self.art = CategoryScraper(CategoryType.ART)
        self.comic = CategoryScraper(CategoryType.COMIC)
        self.other = CategoryScraper(CategoryType.ANOTHER)
        self.all = CategoryScraper(CategoryType.ALL)
        self.article = ArticleScraper()

    async def get_works_by_category(
        self,
        category: CategoryType,
        page: int = 1,
        size: int = 48,
        sort_field: SortField = SortField.RECOMMENDED,
        media_category: Optional[MediaCategory] = None,
    ) -> List[WorkItem]:
        """根据分类获取作品"""
        scraper = CategoryScraper(
            category=category,
            page_number=page,
            page_size=size,
            sort_field=sort_field,
            media_category=media_category,
        )
        return await scraper.get_works()

    async def get_featured_works(
        self,
        page: int = 1,
        size: int = 48,
        sort_field: SortField = SortField.RECOMMENDED,
        media_category: Optional[MediaCategory] = None,
    ) -> List[WorkItem]:
        """获取精选作品"""
        scraper = FeaturedScraper(
            page_number=page,
            page_size=size,
            sort_field=sort_field,
            media_category=media_category,
        )
        return await scraper.get_works()

    async def get_articles(
        self,
        page: int = 1,
        size: int = 48,
        sort_field: SortField = SortField.RECOMMENDED,
    ) -> List[ArticleItem]:
        """获取文章列表"""
        scraper = ArticleScraper(
            page_number=page,
            page_size=size,
            sort_field=sort_field,
        )
        return await scraper.get_articles()

    def get_articles_sync(self, *args, **kwargs) -> List[ArticleItem]:
        """同步方式获取文章列表"""
        return asyncio.run(self.get_articles(*args, **kwargs))
