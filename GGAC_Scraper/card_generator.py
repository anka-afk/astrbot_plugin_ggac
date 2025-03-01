import os
from typing import List, Tuple
from pathlib import Path
import asyncio
from io import BytesIO
from datetime import datetime
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .ggac_scraper import WorkItem
from ..config import FONTS_DIR


class CardGenerator:
    """作品卡片生成器"""

    def __init__(
        self,
        output_dir: str = "cards",
        font_path: str = FONTS_DIR,
        card_width: int = 1000,
        card_padding: int = 30,
        corner_radius: int = 20,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        if not os.path.exists(font_path):
            raise FileNotFoundError(f"找不到字体文件: {font_path}")

        self.font_path = font_path
        self.card_width = card_width
        self.padding = card_padding
        self.corner_radius = corner_radius

        # 颜色配置
        self.colors = {
            "background": "#FFFFFF",
            "title": "#2C3E50",
            "subtitle": "#34495E",
            "text": "#7F8C8D",
            "divider": "#ECF0F1",
            "shadow": "#00000022",
        }

        # 字体大小配置
        self.title_size = 42
        self.subtitle_size = 28
        self.text_size = 24

        try:
            # 加载字体
            self.title_font = ImageFont.truetype(str(font_path), self.title_size)
            self.subtitle_font = ImageFont.truetype(str(font_path), self.subtitle_size)
            self.text_font = ImageFont.truetype(str(font_path), self.text_size)
        except Exception as e:
            raise Exception(f"加载字体文件失败: {e}")

    def _get_text_size(
        self, text: str, font: ImageFont.FreeTypeFont
    ) -> Tuple[int, int]:
        """获取文本尺寸"""
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _wrap_text(
        self, text: str, font: ImageFont.FreeTypeFont, max_width: int
    ) -> List[str]:
        """文本自动换行"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            line = " ".join(current_line)
            w, _ = self._get_text_size(line, font)
            if w > max_width:
                if len(current_line) == 1:
                    lines.append(line)
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(" ".join(current_line))
                    current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))
        return lines

    def _create_text_block(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        start_y: int,
        color: str = "black",
        align: str = "left",
    ) -> int:
        """创建文本块并返回下一个y坐标"""
        lines = self._wrap_text(text, font, self.card_width - 2 * self.padding)
        _, line_height = self._get_text_size("A", font)
        line_spacing = 8

        for line in lines:
            if align == "center":
                w, _ = self._get_text_size(line, font)
                x = (self.card_width - w) // 2
            else:
                x = self.padding

            draw.text((x, start_y), line, font=font, fill=color)
            start_y += line_height + line_spacing

        return start_y + self.padding

    async def _download_image(self, url: str) -> Image.Image:
        """下载图片"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.read()
                    return Image.open(BytesIO(data))
                raise Exception(f"下载图片失败: HTTP {response.status}")

    def _create_rounded_rectangle(
        self, size: Tuple[int, int], radius: int, color: str = "white"
    ) -> Image.Image:
        """创建圆角矩形"""
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)

        # 绘制圆角矩形
        draw.rounded_rectangle([(0, 0), size], radius, fill=255)

        # 创建背景
        image = Image.new("RGB", size, color)

        # 应用圆角遮罩
        return Image.composite(image, Image.new("RGB", size, "white"), mask)

    def _add_shadow(self, image: Image.Image, blur_radius: int = 10) -> Image.Image:
        """添加阴影效果"""
        # 创建阴影
        shadow = Image.new("RGBA", image.size, self.colors["shadow"])
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))

        # 创建新画布
        result = Image.new("RGB", image.size, "white")

        # 组合阴影和原图
        result.paste(shadow, (blur_radius, blur_radius))
        result.paste(image, (0, 0), image.convert("RGBA"))

        return result

    def _draw_divider(
        self, draw: ImageDraw.ImageDraw, y: int, width: int, color: str
    ) -> int:
        """绘制分隔线"""
        line_start = self.padding * 2
        line_width = width - self.padding * 4
        draw.line([(line_start, y), (line_width, y)], fill=color, width=1)
        return y + self.padding

    async def generate_card(self, work: WorkItem) -> Tuple[str, str]:
        """生成单个作品卡片

        返回:
            Tuple[str, str]: (卡片图片路径, 作品链接)
        """
        # 下载并处理封面图片
        cover_image = await self._download_image(work.cover_url)
        cover_width = self.card_width - self.padding * 2
        ratio = cover_width / cover_image.width
        cover_height = int(cover_image.height * ratio)
        cover_image = cover_image.resize((cover_width, cover_height), Image.LANCZOS)

        # 创建圆角封面
        cover_mask = Image.new("L", (cover_width, cover_height), 0)
        cover_draw = ImageDraw.Draw(cover_mask)
        cover_draw.rounded_rectangle(
            [(0, 0), (cover_width, cover_height)], radius=self.corner_radius, fill=255
        )
        cover_image = Image.composite(
            cover_image, Image.new("RGB", cover_image.size, "white"), cover_mask
        )

        # 计算卡片高度
        card_height = (
            self.padding
            + cover_height
            + self.padding * 7
            + self.title_size * 2
            + self.subtitle_size * 3
            + self.text_size * 4
            + self.padding
        )

        # 创建卡片背景
        card = self._create_rounded_rectangle(
            (self.card_width, card_height),
            self.corner_radius,
            self.colors["background"],
        )

        # 粘贴封面
        card.paste(cover_image, (self.padding, self.padding))

        # 创建绘图对象
        draw = ImageDraw.Draw(card)

        # 开始绘制文本
        y = self.padding + cover_height + self.padding * 2

        # 标题
        y = self._create_text_block(
            draw, work.title, self.title_font, y, self.colors["title"], "center"
        )
        y += self.padding

        # 分隔线
        y = self._draw_divider(draw, y, self.card_width, self.colors["divider"])
        y += self.padding * 0.5

        # 作者和创作类型
        author_text = f"作者: {work.username} | 类型: {work.media_category}"
        y = self._create_text_block(
            draw, author_text, self.subtitle_font, y, self.colors["subtitle"]
        )

        # 分类
        categories_text = f"分类: {', '.join(cat.name for cat in work.categories)}"
        y = self._create_text_block(
            draw, categories_text, self.text_font, y, self.colors["text"]
        )

        # 统计信息
        stats_text = f"浏览量: {work.view_count:,} | 热度: {work.hot:,}"
        y = self._create_text_block(
            draw, stats_text, self.text_font, y, self.colors["text"]
        )

        # 创建时间
        time_text = f"创建时间: {work.create_time.strftime('%Y-%m-%d %H:%M:%S')}"
        self._create_text_block(draw, time_text, self.text_font, y, self.colors["text"])

        # 添加阴影效果
        card = self._add_shadow(card)

        # 保存卡片
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        card_filename = f"{work.id}_{timestamp}.png"
        card_path = self.output_dir / card_filename
        card.save(card_path, "PNG", quality=95)

        # 生成作品链接
        work_url = f"https://www.ggac.com/work/detail/{work.id}"

        return str(card_path), work_url

    async def generate_cards(self, works: List[WorkItem]) -> List[Tuple[str, str]]:
        """批量生成作品卡片

        返回:
            List[Tuple[str, str]]: [(卡片图片路径, 作品链接), ...]
        """
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
            media_category="插画",
            categories=[Category("二次元"), Category("原创"), Category("风景")],
            view_count=12345,
            hot=678,
            create_time=datetime.now(),
            cover_url="https://via.placeholder.com/800x600/000000/FFFFFF",
        )

        generator = CardGenerator(output_dir=".")

        card_path, work_url = await generator.generate_card(test_work)
        print(f"卡片已生成: {card_path}")
        print(f"作品链接: {work_url}")

    asyncio.run(main())
