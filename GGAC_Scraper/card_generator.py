import os
from typing import List, Tuple, Optional
from pathlib import Path
import asyncio
from io import BytesIO
from datetime import datetime
import aiohttp
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from ggac_scraper import WorkItem
from config import FONTS_DIR


class CardGenerator:
    """作品卡片生成器"""

    def __init__(
        self,
        output_dir: str = "cards",
        font_path: str = FONTS_DIR,
        min_card_width: int = 600,  # 最小卡片宽度
        max_card_width: int = 1500,  # 最大卡片宽度
        card_padding_ratio: float = 0.033,  # 边距与卡片宽度的比例
    ):
        # ... existing code ...
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        if not os.path.exists(font_path):
            raise FileNotFoundError(f"找不到字体文件: {font_path}")

        self.font_path = font_path
        self.min_card_width = min_card_width
        self.max_card_width = max_card_width
        self.card_padding_ratio = card_padding_ratio

        # 默认值，将在generate_card中动态调整
        self.card_width = 900
        self.padding = int(self.card_width * self.card_padding_ratio)
        self.font_sizes = self._calculate_font_sizes(self.card_width)
        self.fonts = self._load_fonts(self.font_sizes)

        # 主题颜色 - 根据作品类别可动态选择
        self.themes = {
            "插画": {
                "primary": "#FF5722",
                "secondary": "#F57C00",
                "accent": "#FF9800",
                "pattern": "dots",
            },
            "动画": {
                "primary": "#8e44ad",
                "secondary": "#6c3483",
                "accent": "#f1c40f",
                "pattern": "lines",
            },
            "漫画": {
                "primary": "#27ae60",
                "secondary": "#196f3d",
                "accent": "#e67e22",
                "pattern": "circles",
            },
            "3D模型": {
                "primary": "#e74c3c",
                "secondary": "#c0392b",
                "accent": "#e74c3c",
                "pattern": "grid",
            },
            "default": {
                "primary": "#2c3e50",
                "secondary": "#1a2530",
                "accent": "#f39c12",
                "pattern": "grid",
            },
        }

        # 基础颜色配置
        self.colors = {
            "card_bg": "#ffffff",
            "card_bg_alt": "#f9f9f9",
            "text_primary": "#333333",
            "text_secondary": "#666666",
            "text_light": "#999999",
            "highlight": "#FFC107",
            "divider": "#eeeeee",
            "shadow": "#00000020",
            "overlay": "#00000040",
            "follow_btn": "#FFC107",
            "follow_text": "#333333",
            "fire_icon": "#e74c3c",
            "heart_icon": "#e74c3c",  # 添加心形图标颜色
        }

    # ... existing code ...
    def _calculate_font_sizes(self, card_width: int) -> dict:
        """根据卡片宽度计算字体大小"""
        # 基准宽度是900，其他宽度按比例缩放
        base_width = 900
        scale_factor = card_width / base_width

        return {
            "title": max(20, int(38 * scale_factor)),
            "subtitle": max(16, int(24 * scale_factor)),
            "info": max(14, int(22 * scale_factor)),
            "caption": max(12, int(18 * scale_factor)),
            "tag": max(10, int(16 * scale_factor)),
            "follow": max(14, int(20 * scale_factor)),
        }

    def _load_fonts(self, font_sizes: dict) -> dict:
        """加载字体"""
        try:
            return {
                "title": ImageFont.truetype(str(self.font_path), font_sizes["title"]),
                "subtitle": ImageFont.truetype(
                    str(self.font_path), font_sizes["subtitle"]
                ),
                "info": ImageFont.truetype(str(self.font_path), font_sizes["info"]),
                "caption": ImageFont.truetype(
                    str(self.font_path), font_sizes["caption"]
                ),
                "tag": ImageFont.truetype(str(self.font_path), font_sizes["tag"]),
                "follow": ImageFont.truetype(str(self.font_path), font_sizes["follow"]),
            }
        except Exception as e:
            raise Exception(f"加载字体文件失败: {e}")

    def _get_text_dimensions(
        self, text: str, font: ImageFont.FreeTypeFont
    ) -> Tuple[int, int]:
        """获取文本尺寸"""
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _draw_bold_text(self, draw, x, y, text, font, fill):
        """绘制加粗文本（通过多次绘制实现）"""
        # 绘制四周的轮廓来模拟粗体效果
        offsets = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for offset_x, offset_y in offsets:
            draw.text((x + offset_x, y + offset_y), text, font=font, fill=fill)
        # 绘制中心文本
        draw.text((x, y), text, font=font, fill=fill)

    def _create_rounded_mask(self, size: Tuple[int, int], radius: int) -> Image.Image:
        """创建圆角遮罩"""
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), size], radius, fill=255)
        return mask

    def _create_circular_mask(self, size: Tuple[int, int]) -> Image.Image:
        """创建圆形遮罩"""
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)

        # 计算圆的中心和半径
        width, height = size
        center = (width // 2, height // 2)
        radius = min(width, height) // 2

        # 绘制圆形
        draw.ellipse(
            [
                (center[0] - radius, center[1] - radius),
                (center[0] + radius, center[1] + radius),
            ],
            fill=255,
        )

        return mask

    def _apply_design_effect_to_cover(
        self, cover_image: Image.Image, theme: dict
    ) -> Image.Image:
        """对封面图应用设计效果"""
        # 根据图片样式，简化效果处理
        result = cover_image.copy().convert("RGBA")

        # 轻微增强亮度和对比度
        enhancer = ImageEnhance.Brightness(result)
        result = enhancer.enhance(1.05)

        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(1.05)

        return result

    def _create_circular_avatar(
        self, avatar_image: Image.Image, size: int
    ) -> Image.Image:
        """将头像处理成圆形"""
        # 调整头像尺寸为正方形
        avatar = avatar_image.copy()
        avatar = avatar.resize((size, size), Image.LANCZOS)

        # 创建圆形遮罩
        mask = self._create_circular_mask((size, size))

        # 应用遮罩
        avatar.putalpha(mask)

        return avatar

    async def _download_image(self, url: str) -> Optional[Image.Image]:
        """下载图片"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        return Image.open(BytesIO(data)).convert("RGBA")
                    raise Exception(f"下载图片失败: HTTP {response.status}")
        except Exception as e:
            print(f"下载图片出错: {e}")
            # 创建一个默认图片
            default_img = Image.new("RGBA", (800, 600), (200, 200, 200, 255))
            draw = ImageDraw.Draw(default_img)
            draw.text(
                (400, 300),
                "图片加载失败",
                fill=(100, 100, 100, 255),
                font=ImageFont.truetype(str(self.font_path), 24),
                anchor="mm",
            )
            return default_img

    async def generate_card(self, work: WorkItem) -> Tuple[str, str]:
        """生成单个作品卡片，具有现代设计感"""
        # 获取作品适合的主题色
        theme = self.themes.get(work.media_category, self.themes["default"])

        # 下载并处理封面图片
        original_cover = await self._download_image(work.cover_url)
        if not original_cover:
            return None, None

        # 下载用户头像
        avatar_image = None
        if hasattr(work, "user_avatar") and work.user_avatar:
            avatar_image = await self._download_image(work.user_avatar)

        # 根据原始图片大小自适应卡片宽度
        original_width, original_height = original_cover.size

        # 确定卡片宽度，限制在最小和最大范围内
        self.card_width = min(
            max(original_width, self.min_card_width), self.max_card_width
        )

        # 根据新的卡片宽度更新padding和字体大小
        self.padding = int(self.card_width * self.card_padding_ratio)
        self.font_sizes = self._calculate_font_sizes(self.card_width)
        self.fonts = self._load_fonts(self.font_sizes)

        # 调整封面图高度
        # 根据原始图片的宽高比调整封面高度
        if original_width > 0 and original_height > 0:
            aspect_ratio = original_height / original_width
            cover_height = int(self.card_width * aspect_ratio)
            # 限制最大高度，避免太长的图片
            cover_height = min(cover_height, int(self.card_width * 0.8))
            # 确保最小高度
            cover_height = max(cover_height, int(self.card_width * 0.4))
        else:
            cover_height = int(self.card_width * 0.6)  # 默认比例

        # 调整封面图尺寸
        cover_image = Image.new(
            "RGBA", (self.card_width, cover_height), (255, 255, 255, 0)
        )
        # 按比例调整图像大小，保持宽高比
        scaled_cover = original_cover.copy()
        scaled_width = self.card_width
        scaled_height = int(original_height * (scaled_width / original_width))

        # 如果调整后的高度超过了目标高度，则按高度调整
        if scaled_height > cover_height:
            scaled_height = cover_height
            scaled_width = int(original_width * (scaled_height / original_height))

        scaled_cover = scaled_cover.resize((scaled_width, scaled_height), Image.LANCZOS)

        # 将缩放后的图像居中粘贴到空白背景上
        paste_x = (self.card_width - scaled_width) // 2
        paste_y = (cover_height - scaled_height) // 2
        cover_image.paste(scaled_cover, (paste_x, paste_y))

        # 对封面应用设计效果
        enhanced_cover = self._apply_design_effect_to_cover(cover_image, theme)

        # 计算作者栏高度
        author_section_height = int(self.card_width * 0.08)
        author_section_height = max(author_section_height, 60)  # 确保最小高度

        # 预先计算所需的信息区域大小，避免底部空白
        # 计算文本所需的垂直空间
        text_height_title = self.font_sizes["title"] * 1.3
        text_height_category = self.font_sizes["info"] * 1.3
        text_height_stats = self.font_sizes["caption"] * 1.3

        # 添加各元素之间的间距和边距
        spacings = self.padding * 1.7  # 总间距，包括上下边距和元素间距

        # 计算精确的信息区域高度
        info_section_height = int(
            text_height_title + text_height_category + text_height_stats + spacings
        )

        # 确保最小高度
        info_section_height = max(info_section_height, int(self.card_width * 0.15))

        # 计算卡片总高度 - 现在作者栏在封面下方
        card_height = cover_height + author_section_height + info_section_height

        # 创建卡片基础
        card = Image.new("RGBA", (self.card_width, card_height), self.colors["card_bg"])

        # 创建作者栏背景
        author_bg = Image.new(
            "RGBA", (self.card_width, author_section_height), self.colors["card_bg"]
        )

        # 创建底部卡片背景
        info_bg = Image.new(
            "RGBA", (self.card_width, info_section_height), self.colors["card_bg"]
        )

        # 组合卡片 - 现在是封面在顶部，作者栏在中间，信息区域在底部
        card.paste(enhanced_cover, (0, 0))
        card.paste(author_bg, (0, cover_height))
        card.paste(info_bg, (0, cover_height + author_section_height))

        # 创建绘图对象
        draw = ImageDraw.Draw(card)

        # 绘制作者区域分隔线
        draw.line(
            [(0, cover_height), (self.card_width, cover_height)],
            fill=self.colors["divider"],
            width=1,
        )

        # 绘制信息区域分隔线
        draw.line(
            [
                (0, cover_height + author_section_height),
                (self.card_width, cover_height + author_section_height),
            ],
            fill=self.colors["divider"],
            width=1,
        )

        # 绘制作者头像和用户名 - 现在在封面图下方
        avatar_size = int(author_section_height * 0.7)  # 确保头像大小适应作者区域
        avatar_x = self.padding
        avatar_y = cover_height + (author_section_height - avatar_size) // 2

        if avatar_image:
            # 处理头像为圆形
            circular_avatar = self._create_circular_avatar(avatar_image, avatar_size)
            card.paste(circular_avatar, (avatar_x, avatar_y), circular_avatar)
            username_x = avatar_x + avatar_size + self.padding // 2
        else:
            username_x = avatar_x

        # 绘制用户名
        draw.text(
            (
                username_x,
                avatar_y + avatar_size // 2 - self.font_sizes["subtitle"] // 2,
            ),
            work.username,
            font=self.fonts["subtitle"],
            fill=self.colors["text_primary"],
        )

        # 绘制关注按钮 - 现在在封面图下方
        follow_text = "求关注"
        follow_width, follow_height = self._get_text_dimensions(
            follow_text, self.fonts["follow"]
        )
        follow_btn_width = follow_width + self.padding
        follow_btn_height = int(self.font_sizes["follow"] * 1.8)
        follow_btn_x = self.card_width - self.padding - follow_btn_width
        follow_btn_y = cover_height + (author_section_height - follow_btn_height) // 2

        # 绘制黄色关注按钮
        draw.rounded_rectangle(
            [
                (follow_btn_x, follow_btn_y),
                (follow_btn_x + follow_btn_width, follow_btn_y + follow_btn_height),
            ],
            radius=follow_btn_height // 2,
            fill=self.colors["follow_btn"],
        )

        # 绘制关注文本
        text_x = follow_btn_x + (follow_btn_width - follow_width) // 2
        text_y = follow_btn_y + (follow_btn_height - follow_height) // 2
        draw.text(
            (text_x, text_y),
            follow_text,
            font=self.fonts["follow"],
            fill=self.colors["follow_text"],
        )

        # 计算信息区域的具体位置 - 避免空白
        info_top_padding = self.padding // 2  # 减小顶部间距
        info_y = cover_height + author_section_height + info_top_padding

        # 不再绘制红色圆形图标
        title_x = self.padding  # 标题直接从左边距开始，不再有圆形图标

        # 绘制标题 - 左对齐，不再使用加粗效果
        draw.text(
            (title_x, info_y),
            work.title,
            font=self.fonts["title"],
            fill=self.colors["text_primary"],
        )

        # 在标题下方添加类别信息
        category_spacing = int(text_height_title * 0.2)  # 减小垂直间距
        category_y = info_y + text_height_title + category_spacing

        # 处理分类信息
        category_texts = []
        if hasattr(work, "media_category") and work.media_category:
            category_texts.append(work.media_category)

        # 添加额外类别
        for category in work.categories:
            if hasattr(category, "name"):
                category_texts.append(category.name)

        category_text = " | ".join(category_texts)

        # 绘制类别 - 左对齐
        draw.text(
            (self.padding, category_y),
            category_text,
            font=self.fonts["info"],
            fill=self.colors["text_secondary"],
        )

        # 在底部添加更新时间、浏览量和点赞数
        stats_spacing = int(text_height_category * 0.2)  # 减小垂直间距
        stats_y = category_y + text_height_category + stats_spacing

        # 格式化更新时间
        update_time = f"作品更新于：{work.create_time.strftime('%Y-%m-%d %H:%M:%S')}"

        # 绘制更新时间
        draw.text(
            (self.padding, stats_y),
            update_time,
            font=self.fonts["caption"],
            fill=self.colors["text_light"],
        )

        # 计算视图图标的位置和浏览量
        stats_spacing = int(self.card_width * 0.15)
        eye_icon_x = self.card_width - self.padding - stats_spacing - 10

        # 绘制眼睛图标 (使用椭圆绘制)
        eye_width = int(self.font_sizes["caption"] * 1.1)
        eye_height = int(eye_width * 0.65)
        eye_y = stats_y + self.font_sizes["caption"] * 0.15

        # 绘制眼睛外轮廓
        draw.ellipse(
            [(eye_icon_x, eye_y), (eye_icon_x + eye_width, eye_y + eye_height)],
            outline=self.colors["text_light"],
            width=1,
        )

        # 绘制眼睛瞳孔
        pupil_size = eye_width // 3
        draw.ellipse(
            [
                (
                    eye_icon_x + (eye_width - pupil_size) // 2,
                    eye_y + (eye_height - pupil_size) // 2,
                ),
                (
                    eye_icon_x + (eye_width + pupil_size) // 2,
                    eye_y + (eye_height + pupil_size) // 2,
                ),
            ],
            fill=self.colors["text_light"],
        )

        # 绘制浏览量
        draw.text(
            (eye_icon_x + eye_width + 10, stats_y),
            str(work.view_count),
            font=self.fonts["caption"],
            fill=self.colors["text_light"],
        )

        # 绘制心形图标和点赞数 - 使用Unicode符号
        # 设置心形图标的尺寸和位置
        heart_size = int(self.font_sizes["caption"] * 1.2)
        likes_text = str(work.hot)
        likes_width, likes_height = self._get_text_dimensions(
            likes_text, self.fonts["caption"]
        )

        # 先计算点赞数的位置
        likes_x = int(self.card_width - self.padding - likes_width)
        likes_y = int(stats_y)

        # 直接使用Unicode心形符号
        heart_symbol = "♥"
        heart_font = self.fonts["caption"].font_variant(size=int(heart_size * 1.2))

        # 获取心形符号的尺寸
        heart_width, heart_height = self._get_text_dimensions(heart_symbol, heart_font)

        # 计算心形位置 - 确保与点赞数对齐
        heart_x = int(likes_x - heart_width - 5)  # 5像素的间距
        heart_y = int(likes_y - (heart_height - likes_height) // 2)  # 垂直居中对齐

        # 直接绘制心形符号
        heart_color = (
            self.colors["heart_icon"] if "heart_icon" in self.colors else "#FF3B30"
        )
        draw.text((heart_x, heart_y), heart_symbol, font=heart_font, fill=heart_color)

        # 绘制点赞数
        draw.text(
            (likes_x, likes_y),
            likes_text,
            font=self.fonts["caption"],
            fill=self.colors["text_light"],
        )

        # 调试用 - 如果需要检查位置，可以取消注释此行
        # draw.rectangle((heart_x, heart_y, heart_x + heart_width, heart_y + heart_height), outline="blue", width=1)

        # 添加圆角效果
        radius = int(self.card_width * 0.015)  # 圆角大小适应卡片宽度
        mask = self._create_rounded_mask(card.size, radius)
        card.putalpha(mask)

        # 添加边框
        draw.rounded_rectangle(
            [(0, 0), (card.width - 1, card.height - 1)],
            radius=radius,
            outline=self.colors["divider"],
            width=1,
        )

        # 保持RGBA模式以保留透明度
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        card_filename = f"{work.id}_{timestamp}.png"
        card_path = self.output_dir / card_filename
        card.save(card_path, "PNG")

        # 生成作品链接
        work_url = f"https://www.ggac.com/work/detail/{work.id}"

        return str(card_path), work_url

    async def generate_cards(self, works: List[WorkItem]) -> List[Tuple[str, str]]:
        """批量生成作品卡片"""
        tasks = [self.generate_card(work) for work in works]
        return await asyncio.gather(*tasks)


if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    from dataclasses import dataclass

    @dataclass
    class Category:
        name: str
        level: int = 0

    @dataclass
    class TestWorkItem:
        id: int
        title: str
        username: str
        user_avatar: str
        media_category: str
        categories: list
        view_count: int
        hot: int
        create_time: datetime
        cover_url: str

    async def main():
        test_work = TestWorkItem(
            id=12345,
            title="示例作品标题",
            username="小明",
            user_avatar="https://cdn-prd.ggac.com/ggac/user/detail/url/ZP5z35PsDAp8Y6ncxNKAWcyNTaQK78rG1706888761356-500x.jpg",
            media_category="3D模型",
            categories=[
                Category("风景"),
                Category("风景图片"),
            ],
            view_count=360,
            hot=18525,
            create_time=datetime.strptime("2024-11-16 14:03:18", "%Y-%m-%d %H:%M:%S"),
            cover_url="https://picsum.photos/900/600",
        )

        # 使用不同尺寸的图片测试自适应
        test_sizes = [
            "https://picsum.photos/600/400",  # 小尺寸
            "https://picsum.photos/900/600",  # 中等尺寸
            "https://picsum.photos/1200/800",  # 大尺寸
            "https://picsum.photos/1800/1200",  # 超大尺寸
            "https://picsum.photos/1000/2000",  # 竖图
            "https://picsum.photos/2000/500",  # 横图
        ]

        generator = CardGenerator(output_dir=".")

        # 测试不同尺寸的图片
        for i, url in enumerate(test_sizes):
            test_work.id = 12345 + i
            test_work.title = f"测试{i+1}: {url.split('/')[-1]}"
            test_work.cover_url = url

            card_path, work_url = await generator.generate_card(test_work)
            print(f"卡片{i+1}已生成: {card_path}")

    asyncio.run(main())
