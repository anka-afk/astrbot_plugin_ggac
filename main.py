import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.all import *
from astrbot.core.message.message_event_result import MessageChain
from typing import List, Dict
from .GGAC_Scraper.ggac_monitor import GGACMonitor
from .config import CACHE_DIR, CARDS_DIR

@register("ggac_messenger", "anka", "GGAC作品更新推送插件", "1.0.0")
class GGACPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.monitor = GGACMonitor(cache_dir=CACHE_DIR, cards_dir=CARDS_DIR)
        asyncio.create_task(self.monitoring_task())

    async def send_updates_to_groups(self, updates: Dict[str, List[Dict[str, str]]]):
        """向配置的群组发送更新信息"""
        if not any(updates.values()):
            return

        for group_id in self.config.get("target_groups", []):
            # 构造统一消息源
            unified_msg_origin = f"group_{group_id}"

            for category, items in updates.items():
                if not items:
                    continue

                # 发送分类标题
                await self.context.send_message(
                    unified_msg_origin,
                    MessageChain().message(f"发现{category}类型新作品更新:"),
                )

                # 发送每个更新项
                for item in items:
                    chain = (
                        MessageChain()
                        .file_image(item["image_path"])
                        .message(f"\n作品链接: {item['url']}")
                    )
                    await self.context.send_message(unified_msg_origin, chain)

    async def monitoring_task(self):
        """监控任务"""
        interval = self.config.get("check_interval", 300)

        while True:
            try:
                updates = await self.monitor.check_updates()
                await self.send_updates_to_groups(updates)
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
