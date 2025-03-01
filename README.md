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
