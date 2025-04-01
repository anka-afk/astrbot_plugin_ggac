import asyncio
import traceback
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.all import *
from astrbot.core.message.message_event_result import MessageChain
from astrbot.api.message_components import Plain, Image
from astrbot.api.event.filter import EventMessageType
from typing import List, Dict
from .GGAC_Scraper.ggac_monitor import GGACMonitor
from .config import CACHE_DIR, CARDS_DIR, CATEGORY_MAP, load_settings


@register(
    "astrbot_plugin_GGAC_Messenger",
    "anka",
    "anka - GGAC 作品更新推送插件 - 自动监控并推送 GGAC 平台精选作品的更新! 附赠一套 GGAC 网站完整 api! 还有随机抽取 GGAC 内容功能, 详情见github页面!",
    "1.0.0",
)
class GGACPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        # 加载推送设置
        settings = load_settings()

        # 构建推送设置字典
        self.push_settings = {}
        for category_name, settings in settings.items():
            self.push_settings[category_name] = {
                "category": CATEGORY_MAP.get(
                    settings["category"], settings["category"]
                ),
                "media_type": CATEGORY_MAP.get(
                    settings["media_type"], settings["media_type"]
                ),
                "sort_by": CATEGORY_MAP.get(
                    settings.get("sort_by", "推荐"), "recommended"
                ),
            }

        self.monitor = GGACMonitor(cache_dir=CACHE_DIR, cards_dir=CARDS_DIR)
        asyncio.create_task(self.monitoring_task())

    @filter.on_astrbot_loaded()
    async def on_astrbot_loaded(self):
        if not hasattr(self, "client"):
            self.client = self.context.get_platform("aiocqhttp").get_client()
        return

    async def send_updates(
        self, group_id: str, updates: Dict[str, List[Dict[str, str]]]
    ):
        """向指定群组推送更新"""
        if hasattr(self, "client"):
            try:
                all_items = []
                for items in updates.values():
                    all_items.extend(items)

                if not all_items:
                    return

                print(f"向群 {group_id} 推送 {len(all_items)} 个更新")

                for item in all_items:
                    try:
                        message = [
                            {
                                "type": "image",
                                "data": {"file": "file://" + item["image_path"]},
                            },
                            {
                                "type": "text",
                                "data": {"text": f"作品链接: {item['url']}"},
                            },
                        ]

                        payloads = {"group_id": group_id, "message": message}
                        await self.client.api.call_action("send_group_msg", **payloads)
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"推送作品时出错: {e}")
                        traceback.print_exc()
                        continue

            except Exception as e:
                print(f"向群组 {group_id} 推送消息时出错: {e}")
                traceback.print_exc()
        else:
            print("==注意==: 重启后需要发送一条消息获取client, 等待client获取中...")
            while not hasattr(self, "client"):
                await asyncio.sleep(10)
            await self.send_updates(group_id, updates)

    async def monitoring_task(self):
        """监控任务"""
        interval = self.config.get("check_interval", 300)

        while True:
            try:
                updates = await self.monitor.check_updates(self.push_settings)
                if any(updates.values()):
                    target_groups = self.config.get("target_groups", [])
                    if not target_groups:
                        print("未配置目标群组")
                        continue

                    print(f"检测到更新，准备向 {len(target_groups)} 个群组推送")

                    for group_id in target_groups:
                        await self.send_updates(group_id, updates)

                await asyncio.sleep(interval)
            except Exception as e:
                print(f"监控任务出错: {e}")
                await asyncio.sleep(60)

    @filter.command("ggac_status")
    async def check_status(self, event: AstrMessageEvent):
        """检查插件状态"""
        yield event.plain_result(
            f"GGAC监控插件正在运行\n"
            f"目标群组: {', '.join(map(str, self.config.get('target_groups', [])))} \n"
            f"检查间隔: {self.config.get('check_interval', 300)}秒"
        )

    @filter.command("ggac")
    async def get_random_work(
        self, event: AstrMessageEvent, category: str = "all", media_type: str = "2d"
    ):
        """获取随机作品

        Args:
            category: 分类名称，可选值:
                     featured(精选)/game(游戏)/anime(二次元)/movie(影视)/
                     art(文创)/comic(动画漫画)/other(其他)/all(全部)
            media_type: 创作类型，可选值:
                       2d(2D原画)/3d(3D模型)/ui(UI设计)/
                       animation(动画)/vfx(特效)/other(其他)
        """
        try:
            category_map = {
                "featured": "featured",
                "game": "game",
                "anime": "anime",
                "movie": "movie",
                "art": "art",
                "comic": "comic",
                "other": "other",
                "all": "all",
                "精选": "featured",
                "游戏": "game",
                "二次元": "anime",
                "影视": "movie",
                "文创": "art",
                "动画漫画": "comic",
                "其他": "other",
                "全部": "all",
            }

            media_type_map = {
                "2d": "2d",
                "3d": "3d",
                "ui": "ui",
                "animation": "animation",
                "vfx": "vfx",
                "other": "other",
                "2d原画": "2d",
                "3d模型": "3d",
                "ui设计": "ui",
                "动画": "animation",
                "特效": "vfx",
                "其他": "other",
                "原画": "2d",
                "模型": "3d",
                "界面": "ui",
            }

            category_names = {
                "featured": "精选",
                "game": "游戏",
                "anime": "二次元",
                "movie": "影视",
                "art": "文创",
                "comic": "动画漫画",
                "other": "其他",
                "all": "全部",
            }

            media_type_names = {
                "2d": "2D原画",
                "3d": "3D模型",
                "ui": "UI设计",
                "animation": "动画",
                "vfx": "特效",
                "other": "其他",
            }

            category = category.lower()
            media_type = media_type.lower()

            if category not in category_map:
                categories_str = "/".join(
                    [f"{k}({v})" for k, v in category_names.items()]
                )
                yield event.plain_result(
                    f"无效的分类名称: {category}\n支持的分类: {categories_str}"
                )
                return

            if media_type not in media_type_map:
                media_types_str = "/".join(
                    [f"{k}({v})" for k, v in media_type_names.items()]
                )
                yield event.plain_result(
                    f"无效的创作类型: {media_type}\n支持的创作类型: {media_types_str}"
                )
                return

            standard_category = category_map[category]
            standard_media_type = media_type_map[media_type]

            works = await self.monitor.api.get_works(
                category=standard_category,
                media_type=standard_media_type,
                sort_by="latest",
                page=1,
                size=48,
            )

            if not works:
                yield event.plain_result(
                    f"未找到{category_names[standard_category]}分类下的{media_type_names[standard_media_type]}作品"
                )
                return

            import random

            work = random.choice(works)

            card_path, work_url = await self.monitor.card_generator.generate_card(
                work, self.config.get("cover_type", "default")
            )

            message = [
                {
                    "type": "image",
                    "data": {"file": "file://" + card_path},
                },
                {
                    "type": "text",
                    "data": {"text": f"作品链接: {work_url}"},
                },
            ]

            payloads = {"group_id": event.message_obj.group_id, "message": message}
            await self.client.api.call_action("send_group_msg", **payloads)

        except Exception as e:
            print(f"获取随机作品时出错: {e}")
            traceback.print_exc()
            yield event.plain_result(f"获取作品失败: {str(e)}")
        finally:
            event.stop_event()
