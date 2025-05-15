# 🎨 AstrBot GGAC Messenger

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/Python-3.10.14%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen)](CONTRIBUTING.md)
[![Contributors](https://img.shields.io/github/contributors/anka-afk/astrbot_plugin_ggac?color=green)](https://github.com/anka-afk/astrbot_plugin_ggac/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/anka-afk/astrbot_plugin_ggac)](https://github.com/anka-afk/astrbot_plugin_ggac/commits/main)

</div>

<div align="center">

[![Moe Counter](https://count.getloli.com/get/@GGACMessenger?theme=moebooru)](https://github.com/anka-afk/astrbot_plugin_ggac)

</div>

GGAC 作品更新推送插件 - 自动监控并推送 GGAC 平台精选作品的更新!

附赠一套 GGAC 网站完整 api!

## ‼️ 通知: 现在需要填写 GGAC 账号和密码才能获取更新信息!(2025-5-15)

## ✨ 功能特性

- 🔄 自动监控 GGAC 平台作品更新
- 🖼️ 生成精美的作品信息卡片
- 📨 自动推送更新到指定 QQ 群
- 🎯 支持多个目标群组推送
- 🎨 支持获取随机作品展示

## 🛠️ 配置说明

在插件配置中设置以下参数:

```json
{
  "target_groups": {
    "description": "需要推送更新的群组ID列表",
    "type": "list",
    "hint": "填写需要接收GGAC更新推送的群号，如: [123456, 789012]",
    "default": []
  },
  "check_interval": {
    "description": "检查更新的时间间隔(秒)",
    "type": "int",
    "hint": "多久检查一次更新，建议300-600秒",
    "default": 300
  },
  "cover_type": {
    "description": "封面类型",
    "type": "string",
    "hint": "封面类型, 可选: 'detail'(详情), 'default'(默认",
    "default": "default",
    "options": ["detail", "default"]
  },
  "account": {
    "description": "GGAC账号",
    "type": "string",
    "hint": "填写你的GGAC账号, 用于获取更新信息",
    "default": ""
  },
  "password": {
    "description": "GGAC密码",
    "type": "string",
    "hint": "填写你的GGAC密码, 用于获取更新信息",
    "default": ""
  }
}
```

此外, 你可以在 Astrbot/data/ggac_cache/settings 中调整推送内容, 格式参考已有格式, 各个字段可用参数如下:

```json
{
  "推送名称": {
    "category": "推送类别", //可选:精选/游戏/二次元/影视/文创/动画漫画/其他/全部/不指定分类
    "media_type": "推送创作类型", //可选:2D原画/3D模型/UI设计/动画/特效/其他/不指定创作类型
    "sort_by": "推送排序方式" //可选:最新/推荐/浏览量/点赞/热度
  }
}
```

## 📝 使用命令

### 查看插件状态

```
/ggac_status
```

显示当前配置的目标群组和检查间隔

### 获取随机作品

```
/ggac [分类] [创作类型]
```

支持的分类:

- featured(精选)
- game(游戏)
- anime(二次元)
- movie(影视)
- art(文创)
- comic(动画漫画)
- other(其他)
- all(全部)

支持的创作类型:

- 2d(2D 原画)
- 3d(3D 模型)
- ui(UI 设计)
- animation(动画)
- vfx(特效)
- other(其他)

## 🔄 版本历史

- v1.2.0

  - ✅ 现在可以在设置调整推送类别
  - ✅ 现在可以调整推送创作类型
  - ✅ 现在可以自定义推送的详细类别

- v1.0.0
  - ✅ 实现基础的作品监控与推送
  - ✅ 支持生成作品信息卡片
  - ✅ 支持获取随机作品展示

## 👥 贡献指南

欢迎通过以下方式参与项目：

- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码

## 🌟 鸣谢

感谢所有为这个项目做出贡献的开发者！

---

> 让创意流动,让灵感相遇 🎨
