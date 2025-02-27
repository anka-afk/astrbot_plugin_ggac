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
from .config import CACHE_DIR, CARDS_DIR


@register("ggac_messenger", "anka", "GGAC作品更新推送插件", "1.0.0")
class GGACPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.monitor = GGACMonitor(cache_dir=CACHE_DIR, cards_dir=CARDS_DIR)
        self.pending_updates = {}  # 存储待推送的更新
        asyncio.create_task(self.monitoring_task())

    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        """监听群消息，用于推送更新"""
        group_id = event.message_obj.group_id
        if not group_id:
            return

        target_groups = self.config.get("target_groups", [])
        if str(group_id) not in map(str, target_groups):
            return

        if group_id not in self.pending_updates:
            return

        updates = self.pending_updates[group_id]
        if not updates:
            return

        try:
            all_items = []
            for items in updates.values():
                all_items.extend(items)

            if not all_items:
                return

            print(f"向群 {group_id} 推送 {len(all_items)} 个更新")

            for item in all_items:
                try:
                    chain = MessageChain(
                        [
                            Image.fromFileSystem(item["image_path"]),
                            Plain(f"\n作品链接: {item['url']}"),
                        ]
                    )
                    await event.send(chain)
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"推送作品时出错: {e}")
                    traceback.print_exc()
                    continue

            del self.pending_updates[group_id]

        except Exception as e:
            print(f"向群组 {group_id} 推送消息时出错: {e}")
            traceback.print_exc()

    async def cache_updates(self, updates: Dict[str, List[Dict[str, str]]]):
        """缓存需要推送的更新"""
        if not any(updates.values()):
            print("没有需要推送的更新")
            return

        target_groups = self.config.get("target_groups", [])
        if not target_groups:
            print("未配置目标群组")
            return

        print(f"缓存更新内容，等待向 {len(target_groups)} 个群组推送")

        for group_id in target_groups:
            self.pending_updates[group_id] = updates
            print(f"已缓存群 {group_id} 的更新内容")

    async def monitoring_task(self):
        """监控任务"""
        interval = self.config.get("check_interval", 300)

        while True:
            try:
                updates = await self.monitor.check_updates()
                await self.cache_updates(updates)
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"监控任务出错: {e}")
                await asyncio.sleep(60)

    @filter.command("ggac_status")
    async def check_status(self, event: AstrMessageEvent):
        """检查插件状态"""
        pending_groups = list(self.pending_updates.keys())
        yield event.plain_result(
            f"GGAC监控插件正在运行\n"
            f"目标群组: {', '.join(map(str, self.config.get('target_groups', [])))} \n"
            f"检查间隔: {self.config.get('check_interval', 300)}秒\n"
            f"待推送群组: {', '.join(map(str, pending_groups))}"
        )
