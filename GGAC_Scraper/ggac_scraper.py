from typing import Optional, List
from dataclasses import dataclass, field
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
    user_avatar: str
    categories: List[Category]
    view_count: int
    hot: int
    create_time: datetime
    url: str
    detail: Optional[dict] = None

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

        # 确保detail永远不会是None
        detail = data.get("detail", {})
        if detail is None:
            detail = {}

        return cls(
            id=work_id,
            title=data["title"],
            cover_url=data["originalCoverUrl"],
            media_category=media_category,
            username=data["userInfo"]["username"],
            user_avatar=data["userInfo"]["avatarUrl"],
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
            detail=detail,
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
    cookies: Optional[dict] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    headers: Optional[dict] = field(
        default_factory=lambda: {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36 Edg/136.0.0.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "authtype": "1",
            "platform": "2",
            "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "Origin": "https://www.ggac.com",
            "Referer": "https://www.ggac.com/",
        }
    )

    async def ensure_token(self) -> bool:
        """确保token有效，如果无效或不存在则尝试登录"""
        # 如果没有保存凭据，无法自动登录
        if not self.username or not self.password:
            print("[WARNING] No credentials stored for auto-login")
            return False

        # 如果没有token，尝试登录
        if not self.token:
            print("[INFO] No token found, attempting auto-login")
            return await self.login(self.username, self.password)

        return True

    async def login(self, username: str, password: str) -> bool:
        """登录GGAC网站获取认证信息"""
        # 保存凭据以备后续使用
        self.username = username
        self.password = password
        login_url = "https://www.ggac.com/api/user/password_login"
        login_data = {"account": username, "password": password}

        # 登录专用的headers
        login_headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36 Edg/136.0.0.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "Origin": "https://www.ggac.com",
            "Referer": "https://www.ggac.com/auth/login?redirect=https://www.ggac.com/user-center/home/work/list",
            "authtype": "1",
            "platform": "1",
            "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }

        print(f"[DEBUG] 尝试登录: {username}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    login_url, json=login_data, ssl=False, headers=login_headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"[DEBUG] 登录响应: {data}")

                        if data.get("code") == "0":
                            # 保存cookies
                            self.cookies = {
                                cookie.key: cookie.value
                                for cookie in session.cookie_jar
                            }

                            # 保存认证令牌
                            self.token = data.get("data")

                            print(f"[DEBUG] 登录成功，获取到 cookies: {self.cookies}")
                            print(f"[DEBUG] 登录成功，获取到 token: {self.token}")
                            return True
                    print(f"[ERROR] 登录失败: {await response.text()}")
                    return False
            except Exception as e:
                print(f"[ERROR] 登录异常: {e}")
                return False

    async def fetch_with_retry(self, url: str) -> dict:
        """带重试的请求方法"""
        print(f"\n[DEBUG] Requesting URL: {url}")
        await self.ensure_token()

        # 更新请求头，添加认证令牌
        request_headers = self.headers.copy() if self.headers else {}
        if self.token:
            request_headers["authorization"] = self.token
            request_headers["token"] = self.token

        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.get(
                        url, ssl=False, headers=request_headers
                    ) as response:
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

    async def get_work_detail(self, url: str) -> dict:
        # 根据作品的链接获取作品详情
        print(f"[DEBUG] Requesting work detail: {url}")
        await self.ensure_token()

        # 确保引用了正确的域名
        if "m.ggac.com" not in url:
            url = url.replace("www.ggac.com", "m.ggac.com")

        # 为每个详情请求设置特定的Referer
        work_id = url.split("/")[-1]
        detail_headers = self.headers.copy() if self.headers else {}
        detail_headers["Referer"] = f"https://m.ggac.com/work/detail/{work_id}"

        # 添加认证令牌
        if self.token:
            detail_headers["authorization"] = self.token
            detail_headers["token"] = self.token
        else:
            print("[WARNING] No token found, detail requests may fail")

        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.get(
                        url, ssl=False, headers=detail_headers
                    ) as response:
                        if response.status == 200:
                            raw_data = await response.json()
                            # 检查是否需要登录
                            if raw_data.get("code") == "430" and "登录" in raw_data.get(
                                "message", ""
                            ):
                                print(
                                    f"[WARNING] 需要登录才能访问: {raw_data.get('message')}"
                                )
                                return {"error": "need_login"}

                            data = raw_data.get("data")
                            if data is None:
                                print(
                                    f"[WARNING] No data in response for {url}: {raw_data}"
                                )
                                return {}  # 返回空字典而非None
                            return data
                    raise RequestError(
                        f"HTTP {response.status}: {await response.text()}"
                    )
                except Exception as e:
                    print(
                        f"[WARNING] Failed to get work detail (attempt {attempt+1}): {e}"
                    )
                    if attempt == self.max_retries - 1:
                        print(f"[ERROR] All attempts failed for {url}")
                        return {}  # 所有尝试失败时返回空字典
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

        # 为每个作品构建详情URL，使用m.ggac.com域名
        for item in data:
            item["url"] = f"https://m.ggac.com/api/work/detail/{item['id']}"

        # 获取作品详情, 加入进data
        details = await asyncio.gather(
            *(self.get_work_detail(item["url"]) for item in data)
        )
        for item, detail in zip(data, details):
            item["detail"] = detail or {}  # 确保detail是字典而不是None
            if detail:  # 确保detail不是None或空字典
                # 检查是否需要登录
                if isinstance(detail, dict) and detail.get("error") == "need_login":
                    print(f"[ERROR] 无法获取作品 {item['id']} 的详情，需要登录")
                else:
                    item.update(detail)

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

    async def login(self, username: str, password: str) -> bool:
        """登录GGAC网站"""
        base_scraper = BaseScraper()
        success = await base_scraper.login(username, password)
        if success:
            # 更新所有scrapers的cookies和token
            cookies = base_scraper.cookies
            token = base_scraper.token
            for scraper_name in [
                "featured",
                "game",
                "anime",
                "movie",
                "art",
                "comic",
                "other",
                "all",
                "article",
            ]:
                scraper = getattr(self, scraper_name)
                scraper.cookies = cookies
                scraper.token = token
                scraper.username = username
                scraper.password = password
                print(f"[DEBUG] 更新 {scraper_name} 爬虫的token为: {token}")
            print("[DEBUG] 已更新所有爬虫的cookies和token")
        return success

    def login_sync(self, username: str, password: str) -> bool:
        """同步方式登录GGAC网站"""
        return asyncio.run(self.login(username, password))

    async def get_works_by_category(
        self,
        category: CategoryType,
        page: int = 1,
        size: int = 48,
        sort_field: SortField = SortField.RECOMMENDED,
        media_category: Optional[MediaCategory] = None,
    ) -> List[WorkItem]:
        """根据分类获取作品"""
        # 选择合适的已存在爬虫实例
        if category == CategoryType.GAME:
            scraper = self.game
        elif category == CategoryType.ANIME:
            scraper = self.anime
        elif category == CategoryType.MOVIE:
            scraper = self.movie
        elif category == CategoryType.ART:
            scraper = self.art
        elif category == CategoryType.COMIC:
            scraper = self.comic
        elif category == CategoryType.ANOTHER:
            scraper = self.other
        else:  # ALL
            scraper = self.all

        # 更新爬虫参数
        scraper.pageNumber = page
        scraper.pageSize = size
        scraper.sort_field = sort_field
        scraper.media_category = media_category

        return await scraper.get_works()

    async def get_featured_works(
        self,
        page: int = 1,
        size: int = 48,
        sort_field: SortField = SortField.RECOMMENDED,
        media_category: Optional[MediaCategory] = None,
    ) -> List[WorkItem]:
        """获取精选作品"""
        # 使用已有的featured爬虫实例
        self.featured.pageNumber = page
        self.featured.pageSize = size
        self.featured.sort_field = sort_field
        self.featured.media_category = media_category

        return await self.featured.get_works()

    async def get_articles(
        self,
        page: int = 1,
        size: int = 48,
        sort_field: SortField = SortField.RECOMMENDED,
    ) -> List[ArticleItem]:
        """获取文章列表"""
        # 使用已有的article爬虫实例
        self.article.pageNumber = page
        self.article.pageSize = size
        self.article.sort_field = sort_field

        return await self.article.get_articles()

    def get_articles_sync(self, *args, **kwargs) -> List[ArticleItem]:
        """同步方式获取文章列表"""
        return asyncio.run(self.get_articles(*args, **kwargs))
