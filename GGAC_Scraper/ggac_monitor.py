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
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _load_cache(self, cache_file: Path) -> List[Dict]:
        """加载缓存文件"""
        if not cache_file.exists():
            return []

        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_cache(self, cache_file: Path, works: List[WorkItem]):
        """保存缓存文件"""
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
        updates = [work for work in new_works if work.id not in cached_ids]
        if updates:
            print(f"找到 {len(updates)} 个更新")
            for work in updates:
                print(f"新作品: {work.id} - {work.title}")
        return updates

    async def _process_updates(
        self, updates: List[WorkItem], type: str = None
    ) -> List[Dict[str, str]]:
        """处理更新的作品，生成卡片"""
        results = []
        for work in updates:
            try:
                card_path, work_url = await self.card_generator.generate_card(
                    work, type
                )
                results.append(
                    {
                        "image_path": str(Path(card_path).absolute()),
                        "url": work_url,
                        "title": work.title,
                        "id": work.id,
                    }
                )
            except Exception as e:
                print(f"处理作品 {work.id} 时出错: {e}")
                continue
        return results

    def _get_cache_file(self, category_name: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{category_name}.json"

    async def check_updates(
        self, push_settings: dict
    ) -> Dict[str, List[Dict[str, str]]]:
        """检查更新

        Args:
            push_settings: 推送设置字典，格式如:
                {
                    "精选2D": {
                        "category": "featured",
                        "media_type": "2d",
                        "sort_by": "recommended"
                    },
                    "热门3D": {
                        "category": "featured",
                        "media_type": "3d",
                        "sort_by": "hot"
                    }
                }
        """
        results = {}
        try:
            for category_name, settings in push_settings.items():
                # 获取作品
                works = await self.api.get_works(
                    category=settings.get("category"),
                    media_type=settings.get("media_type"),
                    sort_by=settings.get("sort_by", "recommended"),
                )
                print(f"获取到 {len(works)} 个作品 (类别: {category_name})")

                # 获取缓存
                cache_file = self._get_cache_file(category_name)
                cached_data = self._load_cache(cache_file)
                print(f"已缓存 {len(cached_data)} 个作品 (类别: {category_name})")

                if not cached_data:  # 首次运行
                    print(f"首次运行，创建缓存 (类别: {category_name})")
                    self._save_cache(cache_file, works)
                else:
                    updates = self._find_updates(works, cached_data)
                    if updates:
                        print(f"处理 {len(updates)} 个更新 (类别: {category_name})")
                        results[category_name] = await self._process_updates(updates)
                        self._save_cache(cache_file, works)

        except Exception as e:
            print(f"检查更新时出错: {e}")
            import traceback

            traceback.print_exc()
            raise

        return results

    async def start_monitoring(self, push_settings: dict, interval_seconds: int = 300):
        """开始定时监控"""
        while True:
            try:
                updates = await self.check_updates(push_settings)
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
