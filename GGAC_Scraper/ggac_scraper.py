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
        return cls(
            id=work_id,
            title=data["title"],
            cover_url=data["originalCoverUrl"],
            media_category=data["dictMap"]["mediaCategory"],
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
    """基础爬虫类
    ================================================
    api构造:
    精选页面:
    https://www.ggac.com/api/work/list?pageNumber={self.pageNumber}&pageSize={self.pageSize}&isPublic=1&isRecommend=1&sortField={self.sortField}
    全部页面:
    https://www.ggac.com/api/work/list?pageNumber=1&pageSize=48&isPublic=1&sortField=lastSubmitTime
    游戏页面:
    https://www.ggac.com/api/work/list?pageNumber=1&pageSize=48&isPublic=1&categoryId=1&sortField=recommendUpdateTime
    影视页面:
    https://www.ggac.com/api/work/list?pageNumber=1&pageSize=48&isPublic=1&categoryId=3&sortField=recommendUpdateTime
    动画漫画页面:
    https://www.ggac.com/api/work/list?pageNumber=1&pageSize=48&isPublic=1&categoryId=5&sortField=recommendUpdateTime
    二次元页面:
    https://www.ggac.com/api/work/list?pageNumber=1&pageSize=48&isPublic=1&categoryId=2&sortField=recommendUpdateTime
    文创,潮流,艺术页面:
    https://www.ggac.com/api/work/list?pageNumber=1&pageSize=48&isPublic=1&categoryId=4&sortField=recommendUpdateTime
    文章页面:
    https://www.ggac.com/api/global_search/post?pageSize=48&pageNumber=1&dataTable=article&sortField=recommendUpdateTime
    其他页面:
    https://www.ggac.com/api/work/list?pageNumber=1&pageSize=48&isPublic=1&categoryId=17&sortField=recommendUpdateTime
    ================================================
    创作类型:
    参考:
    https://www.ggac.com/api/work/list?pageNumber=1&pageSize=48&isPublic=1&sortField=recommendUpdateTime&isRecommend=1&mediaCategory=1
    mediaCategory字段:
    1.2D原画
    2.3D模型
    4.UI设计
    5.ANI动画
    6.其他
    7.VFX特效
    ================================================

    请求返回示例:
    例如get精选页面:https://www.ggac.com/api/work/list?pageNumber=1&pageSize=2&isPublic=1&isRecommend=1&sortField=recommendUpdateTime
    返回值:
    {
    "code": "0",
    "message": "成功",
    "data": {
        "pageNumber": 1,
        "pageSize": 2,
        "totalPage": 38026,
        "totalSize": 76052,
        "currentSize": 2,
        "pageData": [
        {
            "viewCount": 129,
            "hot": 6700,
            "onRanking": 0,
            "hotLevel": 0,
            "recommendLevel": 1,
            "id": 1770552,
            "title": "暗黑舞者",
            "userId": 822649,
            "coverUrl": "https://cdn-prd.ggac.com/ggac/work/cover/2025/2/17/df0eece8-d814-4e7e-8fea-0894fe18c885-900x.jpg",
            "originalCoverUrl": "https://cdn-prd.ggac.com/ggac/work/cover/2025/2/17/df0eece8-d814-4e7e-8fea-0894fe18c885-900x.jpg",
            "publishType": null,
            "isContest": 0,
            "mediaCategory": 1,
            "isDraft": 0,
            "twinId": 1770551,
            "isPublic": 1,
            "onSale": 1,
            "status": 2,
            "refuseReason": null,
            "offSaleReason": null,
            "createTime": "2025-02-17 11:37:25",
            "updateTime": "2025-02-26 17:15:18",
            "submitTime": "2025-02-17 11:37:21",
            "publishTime": "2025-02-17 11:37:25",
            "lastSubmitTime": "2025-02-26 17:15:15",
            "lastPublishTime": "2025-02-26 17:15:18",
            "dictMap": {
            "mediaCategory": "2D原画",
            "theme": null,
            "themeA": null,
            "team": null
            },
            "userInfo": {
            "id": 822649,
            "username": "阿蓝是有猫人士",
            "avatarUrl": "https://cdn-prd.ggac.com/ggac/user/detail/url/xcTXcxhktHzPFsm7MRrfZECxZsCtYPtG1739345587903-500x.jpg",
            "profession": null,
            "certifiedRoleId": null
            },
            "categoryList": [
            {
                "id": 1,
                "level": 1,
                "name": "游戏",
                "code": "youxi",
                "dataId": 1770552
            },
            {
                "id": 6,
                "level": 2,
                "name": "游戏美宣",
                "code": "yxmx",
                "dataId": 1770552
            }
            ],
            "prizeList": [],
            "recommendJudgeInfos": [],
            "contest": null,
            "mediaTypeList": [1, 10],
            "creatorCount": 0
        },
        {
            "viewCount": 7,
            "hot": 350,
            "onRanking": 0,
            "hotLevel": 0,
            "recommendLevel": 1,
            "id": 1773331,
            "title": "寡妇商人",
            "userId": 822649,
            "coverUrl": "https://cdn-prd.ggac.com/ggac/work/cover/2025/2/26/5d2b0226-d04e-4cec-805f-0896404e7ddd-900x.jpg",
            "originalCoverUrl": "https://cdn-prd.ggac.com/ggac/work/cover/2025/2/26/5d2b0226-d04e-4cec-805f-0896404e7ddd.png",
            "publishType": null,
            "isContest": 0,
            "mediaCategory": 1,
            "isDraft": 0,
            "twinId": 1773330,
            "isPublic": 1,
            "onSale": 1,
            "status": 2,
            "refuseReason": null,
            "offSaleReason": null,
            "createTime": "2025-02-26 17:18:34",
            "updateTime": "2025-02-26 17:30:47",
            "submitTime": "2025-02-26 17:18:29",
            "publishTime": "2025-02-26 17:18:34",
            "lastSubmitTime": "2025-02-26 17:18:29",
            "lastPublishTime": "2025-02-26 17:18:34",
            "dictMap": {
            "mediaCategory": "2D原画",
            "theme": null,
            "themeA": null,
            "team": null
            },
            "userInfo": {
            "id": 822649,
            "username": "阿蓝是有猫人士",
            "avatarUrl": "https://cdn-prd.ggac.com/ggac/user/detail/url/xcTXcxhktHzPFsm7MRrfZECxZsCtYPtG1739345587903-500x.jpg",
            "profession": null,
            "certifiedRoleId": null
            },
            "categoryList": [
            {
                "id": 1,
                "level": 1,
                "name": "游戏",
                "code": "youxi",
                "dataId": 1773331
            },
            {
                "id": 6,
                "level": 2,
                "name": "游戏美宣",
                "code": "yxmx",
                "dataId": 1773331
            }
            ],
            "prizeList": [],
            "recommendJudgeInfos": [],
            "contest": null,
            "mediaTypeList": [1, 10],
            "creatorCount": 0
        }
        ]
    },
    "reqId": "4c18bebcd3cf4a8aa4c9474654e4cbd3",
    "reqTime": "2025-02-26 17:57:26"
    }
    """

    pageNumber: int = 1
    pageSize: int = 48
    sort_field: SortField = SortField.RECOMMENDED
    media_category: Optional[MediaCategory] = None
    headers: dict = None
    base_url: str = "https://www.ggac.com/api"
    cookies: dict = None
    max_retries: int = 3
    retry_delay: float = 1.0

    def __post_init__(self):
        """初始化请求头"""
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-hans",
            "Connection": "keep-alive",
            "Host": "www.ggac.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
            "authType": "1",
            "platform": "1",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }
        self.cookies = {
            "__qc_wId": "864",
            "Hm_lvt_cdb0ed4fefe7f3d410e93c160b2eac6c": "1740387403,1740498141,1740540473,1740562340",
            "HMACCOUNT": "A5AF46EA95DB060D",
            "Hm_lpvt_cdb0ed4fefe7f3d410e93c160b2eac6c": "1740570486",
        }

    def _get_referer(self, category: Optional[CategoryType] = None) -> str:
        """根据不同分类生成对应的 Referer"""
        if category:
            return f"https://www.ggac.com/explore?categoryPid={category}&pageNumber={self.pageNumber}&sortField={self.sort_field}"
        return f"https://www.ggac.com/explore?pageNumber={self.pageNumber}&sortField={self.sort_field}"

    async def fetch_with_retry(self, url: str, headers: dict) -> dict:
        """带重试的请求方法"""
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(cookies=self.cookies) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        raise RequestError(
                            f"HTTP {response.status}: {await response.text()}"
                        )
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def fetch_data(self) -> dict:
        url = self._build_url()
        headers = self.headers.copy()
        if isinstance(self, CategoryScraper):
            headers["Referer"] = self._get_referer(self.category)
        else:
            headers["Referer"] = self._get_referer()

        return await self.fetch_with_retry(url, headers)

    def _build_url(self) -> str:
        """构建基础URL"""
        url = f"{self.base_url}/work/list?pageNumber={self.pageNumber}&pageSize={self.pageSize}&isPublic=1"
        if self.media_category:
            url += f"&mediaCategory={self.media_category}"
        return url

    @staticmethod
    def parse_response(response: dict) -> List[dict]:
        """解析响应数据"""
        if response.get("code") != "0":
            raise Exception(f"请求失败: {response.get('message')}")
        return response.get("data", {}).get("pageData", [])

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
        url = f"{self.base_url}/work/list?pageNumber={self.pageNumber}&pageSize={self.pageSize}&isPublic=1&isRecommend=1&sortField={self.sort_field}"
        if self.media_category:
            url += f"&mediaCategory={self.media_category}"
        print(url)
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
        url += f"&sortField={self.sort_field}"
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
