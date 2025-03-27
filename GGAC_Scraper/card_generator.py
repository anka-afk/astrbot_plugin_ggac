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
from .ggac_scraper import WorkItem
from ..config import FONTS_DIR


class CardGenerator:
    """作品卡片生成器"""

    def __init__(
        self,
        output_dir: str = "cards",
        font_path: str = FONTS_DIR,
        card_width: int = 1200,
        card_padding: int = 30,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        if not os.path.exists(font_path):
            raise FileNotFoundError(f"找不到字体文件: {font_path}")

        self.font_path = font_path
        self.card_width = card_width
        self.padding = card_padding

        # 主题颜色 - 根据作品类别可动态选择
        self.themes = {
            "插画": {
                "primary": "#FFC107",  # 更改为金黄色主题
                "secondary": "#F57C00",
                "accent": "#FF5722",
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
            "card_bg_alt": "#f9f9f9",  # 更淡的背景色
            "text_primary": "#333333",
            "text_secondary": "#555555",
            "text_light": "#777777",
            "highlight": "#FFC107",  # 黄金色高亮
            "divider": "#eeeeee",
            "shadow": "#00000030",
            "overlay": "#00000066",
        }

        # 字体大小配置
        self.font_sizes = {
            "title": 40,  # 减小标题字体大小
            "subtitle": 28,  # 减小副标题字体大小
            "info": 24,  # 减小信息字体大小
            "caption": 20,  # 减小说明字体大小
            "tag": 18,  # 减小标签字体大小
        }

        try:
            # 加载字体
            self.fonts = {
                "title": ImageFont.truetype(str(font_path), self.font_sizes["title"]),
                "subtitle": ImageFont.truetype(
                    str(font_path), self.font_sizes["subtitle"]
                ),
                "info": ImageFont.truetype(str(font_path), self.font_sizes["info"]),
                "caption": ImageFont.truetype(
                    str(font_path), self.font_sizes["caption"]
                ),
                "tag": ImageFont.truetype(str(font_path), self.font_sizes["tag"]),
            }
        except Exception as e:
            raise Exception(f"加载字体文件失败: {e}")

    def _get_text_dimensions(
        self, text: str, font: ImageFont.FreeTypeFont
    ) -> Tuple[int, int]:
        """获取文本尺寸"""
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _create_gradient_background(
        self, size: Tuple[int, int], color1: str, color2: str, direction="vertical"
    ) -> Image.Image:
        """创建渐变背景，支持垂直和水平渐变"""

        # 将十六进制颜色转换为RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip("#")
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)

        width, height = size
        image = Image.new("RGB", size, color1)
        draw = ImageDraw.Draw(image)

        if direction == "vertical":
            for y in range(height):
                r = rgb1[0] + (rgb2[0] - rgb1[0]) * y // height
                g = rgb1[1] + (rgb2[1] - rgb1[1]) * y // height
                b = rgb1[2] + (rgb2[2] - rgb1[2]) * y // height
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        else:  # horizontal
            for x in range(width):
                r = rgb1[0] + (rgb2[0] - rgb1[0]) * x // width
                g = rgb1[1] + (rgb2[1] - rgb1[1]) * x // width
                b = rgb1[2] + (rgb2[2] - rgb1[2]) * x // width
                draw.line([(x, 0), (x, height)], fill=(r, g, b))

        return image

    def _add_pattern(
        self, image: Image.Image, pattern_type: str, theme: dict, opacity: float = 0.07
    ) -> Image.Image:
        """添加图案纹理"""
        pattern = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(pattern)

        width, height = image.size
        primary_color = theme["primary"].lstrip("#")
        r, g, b = tuple(int(primary_color[i : i + 2], 16) for i in (0, 2, 4))
        color = (r, g, b, int(255 * opacity))

        if pattern_type == "dots":
            # 点状图案
            spacing = 30
            dot_size = 3
            for x in range(0, width, spacing):
                for y in range(0, height, spacing):
                    draw.ellipse([(x, y), (x + dot_size, y + dot_size)], fill=color)

        elif pattern_type == "lines":
            # 线状图案
            spacing = 50
            for y in range(0, height, spacing):
                draw.line([(0, y), (width, y)], fill=color, width=1)
            for x in range(0, width, spacing):
                draw.line([(x, 0), (x, height)], fill=color, width=1)

        elif pattern_type == "circles":
            # 圆形图案
            for _ in range(10):
                size = random.randint(50, 200)
                x = random.randint(0, width)
                y = random.randint(0, height)
                draw.ellipse(
                    [(x - size, y - size), (x + size, y + size)], outline=color, width=2
                )

        elif pattern_type == "grid":
            # 网格图案
            spacing = 40
            for x in range(0, width, spacing):
                draw.line([(x, 0), (x, height)], fill=color, width=1)
            for y in range(0, height, spacing):
                draw.line([(0, y), (width, y)], fill=color, width=1)

        return Image.alpha_composite(image.convert("RGBA"), pattern)

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
        # 原始尺寸
        width, height = cover_image.size

        # 增强对比度和饱和度
        enhancer = ImageEnhance.Contrast(cover_image)
        cover_image = enhancer.enhance(1.3)  # 增加对比度
        enhancer = ImageEnhance.Color(cover_image)
        cover_image = enhancer.enhance(1.2)  # 增加饱和度

        # 应用轻微锐化
        cover_image = cover_image.filter(ImageFilter.SHARPEN)

        # 创建带遮罩的图像
        result = cover_image.copy().convert("RGBA")
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 绘制渐变遮罩
        for y in range(height):
            opacity = min(160, int((y / height) * 220))  # 增强底部暗化效果
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, opacity))

        # 添加主题色调
        primary_color = theme["primary"].lstrip("#")
        r, g, b = tuple(int(primary_color[i : i + 2], 16) for i in (0, 2, 4))
        color_overlay = Image.new(
            "RGBA", (width, height), (r, g, b, 40)
        )  # 增加颜色覆盖强度

        # 组合图层
        result = Image.alpha_composite(result, overlay)
        result = Image.alpha_composite(result, color_overlay)

        # 添加轻微的晕影效果
        vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        vignette_draw = ImageDraw.Draw(vignette)

        # 创建圆形径向渐变
        center_x, center_y = width // 2, height // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)

        for x in range(width):
            for y in range(height):
                dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                # 晕影强度，从边缘到中心递减
                opacity = int(min(80, (dist / max_dist) * 150))
                if opacity > 0:
                    vignette_draw.point((x, y), fill=(0, 0, 0, opacity))

        result = Image.alpha_composite(result, vignette)

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

        # 创建背景
        result = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        result.paste(avatar, (0, 0), avatar)

        return result

    def _draw_icon_and_text(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        icon_type: str,
        text: str,
        color: str,
        accent_color: str = None,
    ) -> int:
        """绘制图标和文本，带有强调色"""
        font = self.fonts["caption"]
        icon_size = self.font_sizes["caption"]

        # 字符替代表情符号，使用更简单的字符
        icons = {
            "view": "♨",  # 替代眼睛图标
            "hot": "★",  # 替代火图标
            "time": "◷",  # 替代时钟图标
            "user": "♟",  # 替代用户图标
            "type": "◉",  # 替代艺术图标
            "category": "◈",  # 替代标签图标
            "id": "#",  # 替代ID图标
        }

        # 绘制图标
        icon = icons.get(icon_type, "•")
        icon_color = accent_color if accent_color else color

        # 使用绘制矩形作为备选方案
        if icon_type == "view":
            # 绘制一个眼睛形状
            eye_w, eye_h = 18, 12
            draw.ellipse(
                [(x, y + 4), (x + eye_w, y + eye_h + 4)], outline=icon_color, width=2
            )
            draw.ellipse([(x + 6, y + 7), (x + 12, y + 13)], fill=icon_color)
        elif icon_type == "hot":
            # 绘制一个星星或火形状
            points = [
                (x + 9, y),
                (x + 12, y + 6),
                (x + 18, y + 6),
                (x + 14, y + 10),
                (x + 16, y + 16),
                (x + 9, y + 12),
                (x + 2, y + 16),
                (x + 4, y + 10),
                (x + 0, y + 6),
                (x + 6, y + 6),
            ]
            draw.polygon(points, fill=icon_color)
        else:
            # 对于其他图标使用文字
            draw.text((x, y), icon, font=font, fill=icon_color)

        # 绘制文本
        text_x = x + icon_size + 10  # 增加间距确保不重叠
        draw.text((text_x, y), text, font=font, fill=color)

        # 返回下一个元素的y坐标
        _, text_height = self._get_text_dimensions(text, font)
        return y + text_height + 8  # 减少垂直间距

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
                font=self.fonts["subtitle"],
                anchor="mm",
            )
            return default_img

    async def generate_card(self, work: WorkItem) -> Tuple[str, str]:
        """生成单个作品卡片，具有现代设计感"""
        # 获取作品适合的主题色
        theme = self.themes.get(work.media_category, self.themes["default"])

        # 下载并处理封面图片
        cover_image = await self._download_image(work.cover_url)
        if not cover_image:
            return None, None

        # 下载用户头像
        avatar_image = None
        if hasattr(work, "user_avatar") and work.user_avatar:
            avatar_image = await self._download_image(work.user_avatar)

        # 调整封面图的宽高比更接近正方形
        cover_width = self.card_width
        cover_height = int(cover_width * 0.75)  # 使用更接近图片中显示的比例
        cover_image = cover_image.resize((cover_width, cover_height), Image.LANCZOS)

        # 对封面应用设计效果 - 简化效果处理使其更接近图片
        enhanced_cover = self._apply_design_effect_to_cover(cover_image, theme)

        # 简化信息区域高度计算
        info_section_height = 170  # 减小信息区域高度，更像图片样式

        # 计算卡片总高度
        card_height = cover_height + info_section_height

        # 创建卡片基础
        card = Image.new("RGBA", (self.card_width, card_height), self.colors["card_bg"])

        # 创建底部卡片背景 - 使用纯白色背景
        info_bg = Image.new(
            "RGBA", (self.card_width, info_section_height), self.colors["card_bg"]
        )

        # 组合卡片
        card.paste(enhanced_cover, (0, 0))
        card.paste(info_bg, (0, cover_height), info_bg)

        # 创建绘图对象
        draw = ImageDraw.Draw(card)

        # 添加标题和分类信息
        title_y = cover_height + 30  # 标题位置调整

        # 计算标题文本尺寸以居中显示
        title_width, title_height = self._get_text_dimensions(
            work.title, self.fonts["title"]
        )
        title_x = (self.card_width - title_width) // 2  # 居中计算

        # 绘制标题 - 居中
        draw.text(
            (title_x, title_y),
            work.title,
            font=self.fonts["title"],
            fill=self.colors["text_primary"],
        )

        # 在标题下方添加类别信息 - 2D原画|插图格式，也居中显示
        category_y = title_y + self.font_sizes["title"] + 10

        # 获取类别的分割线|右边的文本
        for category in work.categories:
            if category.level == 2:
                category_text = category.name
        if not category_text:
            category_text = work.categories[0].name

        category_text = f"{work.media_category} | {category_text} "

        # 计算类别文本宽度用于居中
        category_width, _ = self._get_text_dimensions(category_text, self.fonts["info"])
        category_x = (self.card_width - category_width) // 2  # 居中计算

        # 绘制类别 - 居中
        draw.text(
            (category_x, category_y),
            category_text,
            font=self.fonts["info"],
            fill=theme["primary"],  # 使用主题色
        )

        # 设置底部信息栏的垂直位置
        info_row_y = category_y + self.font_sizes["info"] + 20

        # 计算底部信息区域需要的总宽度，以便居中放置
        # 1. 头像和用户名
        avatar_size = 25  # 减小头像大小
        username_width, _ = self._get_text_dimensions(
            work.username, self.fonts["caption"]
        )
        username_space = avatar_size + 8 + username_width  # 头像 + 间距 + 用户名

        # 2. 眼睛图标和浏览量
        eye_width = 18  # 眼睛图标宽度
        view_text = f"{work.view_count}"
        view_width, _ = self._get_text_dimensions(view_text, self.fonts["caption"])
        view_space = eye_width + 8 + view_width  # 眼睛图标 + 间距 + 浏览量

        # 3. 心形图标和点赞数
        heart_width = 20  # 心形图标宽度
        like_text = f"{work.hot}"
        like_width, _ = self._get_text_dimensions(like_text, self.fonts["caption"])
        like_space = heart_width + 8 + like_width  # 心形图标 + 间距 + 点赞数

        # 计算元素之间的间距
        element_spacing = 30  # 元素之间的间距

        # 计算总宽度
        total_width = (
            username_space + element_spacing + view_space + element_spacing + like_space
        )

        # 计算起始位置使整体居中
        start_x = (self.card_width - total_width) // 2

        # 绘制用户头像和用户名
        user_x = start_x

        if avatar_image:
            # 处理头像为圆形
            circular_avatar = self._create_circular_avatar(avatar_image, avatar_size)

            # 计算头像垂直位置
            avatar_y = info_row_y - 2  # 微调使头像垂直居中

            # 添加头像到卡片
            card.paste(circular_avatar, (user_x, avatar_y), circular_avatar)

            # 用户名位置在头像右侧
            username_x = user_x + avatar_size + 8
        else:
            # 没有头像时，用户名位置不变
            username_x = user_x

        # 绘制用户名
        draw.text(
            (username_x, info_row_y),
            work.username,
            font=self.fonts["caption"],
            fill=self.colors["text_secondary"],
        )

        # 计算浏览量起始位置
        view_x = start_x + username_space + element_spacing

        # 绘制眼睛图标
        eye_w, eye_h = 18, 12
        eye_y = info_row_y + 4  # 微调位置使其垂直居中

        # 绘制眼睛外框
        draw.ellipse(
            [(view_x, eye_y), (view_x + eye_w, eye_y + eye_h)],
            outline=self.colors["text_secondary"],
            width=2,
        )

        # 绘制眼睛瞳孔
        draw.ellipse(
            [(view_x + 6, eye_y + 3), (view_x + 12, eye_y + 9)],
            fill=self.colors["text_secondary"],
        )

        # 绘制浏览量数字
        draw.text(
            (view_x + eye_w + 8, info_row_y),
            view_text,
            font=self.fonts["caption"],
            fill=self.colors["text_secondary"],
        )

        # 计算点赞数起始位置
        like_x = view_x + view_space + element_spacing

        # 绘制心形图标
        draw.text(
            (like_x, info_row_y),
            "♥",
            font=self.fonts["caption"],
            fill=theme["accent"],
        )

        # 绘制点赞数
        draw.text(
            (like_x + heart_width, info_row_y),
            like_text,
            font=self.fonts["caption"],
            fill=self.colors["text_secondary"],
        )

        # 添加圆角 - 更大的圆角效果
        mask = self._create_rounded_mask(card.size, 15)  # 更小的圆角
        card.putalpha(mask)

        # 添加卡片边框 - 简单细线边框
        draw.rounded_rectangle(
            [(0, 0), (card.width - 1, card.height - 1)],
            radius=15,
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
            title="测试作品标题 - 一个非常精彩的创作",
            username="创作者小明",
            user_avatar="https://cdn-prd.ggac.com/ggac/user/detail/url/ZP5z35PsDAp8Y6ncxNKAWcyNTaQK78rG1706888761356-500x.jpg",
            media_category="插画",
            categories=[Category("二次元"), Category("原创"), Category("风景")],
            view_count=12345,
            hot=678,
            create_time=datetime.now(),
            cover_url="https://picsum.photos/800/600",
        )

        generator = CardGenerator(output_dir=".")
        card_path, work_url = await generator.generate_card(test_work)
        print(f"卡片已生成: {card_path}")
        print(f"作品链接: {work_url}")

    asyncio.run(main())
