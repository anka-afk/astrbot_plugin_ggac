import json
from pathlib import Path
from typing import List, Dict
import asyncio
from datetime import datetime
from .ggac_api import GGACAPI
from .ggac_scraper import WorkItem
from .card_generator import CardGenerator


class GGACMonitor:
    """GGAC更新监控器"""

    def __init__(self, cache_dir: str = "cache", cards_dir: str = "cards"):
        self.api = GGACAPI()
        self.card_generator = CardGenerator(output_dir=cards_dir)

        # 创建缓存目录
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # 缓存文件路径
        self.cache_files = {
            "2d": self.cache_dir / "featured_2d.json",
            "3d": self.cache_dir / "featured_3d.json",
        }

    def _load_cache(self, cache_file: Path) -> List[Dict]:
        """加载缓存文件"""
        if not cache_file.exists():
            return []

        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_cache(self, cache_file: Path, works: List[WorkItem]):
        """保存缓存文件"""
        # 将WorkItem对象转换为可序列化的字典
        cache_data = [
            {
                "id": work.id,
                "title": work.title,
                "cover_url": work.cover_url,
                "media_category": work.media_category,
                "username": work.username,
                "view_count": work.view_count,
                "hot": work.hot,
                "create_time": work.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "url": work.url,
                "categories": [
                    {
                        "id": cat.id,
                        "level": cat.level,
                        "name": cat.name,
                        "code": cat.code,
                    }
                    for cat in work.categories
                ],
            }
            for work in works
        ]

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def _find_updates(
        self, new_works: List[WorkItem], cached_data: List[Dict]
    ) -> List[WorkItem]:
        """查找更新的作品"""
        cached_ids = {item["id"] for item in cached_data}
        return [work for work in new_works if work.id not in cached_ids]

    async def _process_updates(self, updates: List[WorkItem]) -> List[Dict[str, str]]:
        """处理更新的作品，生成卡片"""
        results = []
        for work in updates:
            card_path, work_url = await self.card_generator.generate_card(work)
            results.append(
                {"image_path": str(Path(card_path).absolute()), "url": work_url}
            )
        return results

    async def check_updates(self) -> Dict[str, List[Dict[str, str]]]:
        """检查更新"""
        results = {"2d": [], "3d": []}

        # 检查2D原画更新
        works_2d = await self.api.get_works(
            category="featured", media_type="2d", sort_by="recommended"
        )
        cached_2d = self._load_cache(self.cache_files["2d"])

        if not cached_2d:  # 首次运行
            self._save_cache(self.cache_files["2d"], works_2d)
        else:
            updates_2d = self._find_updates(works_2d, cached_2d)
            if updates_2d:
                results["2d"] = await self._process_updates(updates_2d)
                self._save_cache(self.cache_files["2d"], works_2d)

        # 检查3D模型更新
        works_3d = await self.api.get_works(
            category="featured", media_type="3d", sort_by="recommended"
        )
        cached_3d = self._load_cache(self.cache_files["3d"])

        if not cached_3d:  # 首次运行
            self._save_cache(self.cache_files["3d"], works_3d)
        else:
            updates_3d = self._find_updates(works_3d, cached_3d)
            if updates_3d:
                results["3d"] = await self._process_updates(updates_3d)
                self._save_cache(self.cache_files["3d"], works_3d)

        return results

    async def start_monitoring(self, interval_seconds: int = 300):
        """开始定时监控"""
        while True:
            try:
                updates = await self.check_updates()
                if any(updates.values()):
                    print(f"发现更新: {datetime.now()}")
                    for category, items in updates.items():
                        if items:
                            print(f"{category}类型更新数量: {len(items)}")
                            for item in items:
                                print(f"图片路径: {item['image_path']}")
                                print(f"作品链接: {item['url']}")
                                print("---")

                await asyncio.sleep(interval_seconds)
            except Exception as e:
                print(f"监控出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续
