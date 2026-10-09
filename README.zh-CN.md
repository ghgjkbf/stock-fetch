# stock-fetch

[English](README.md) | 中文

**一条命令检索并下载免费许可素材——图片、视频、音乐、音效——自动归类进本地素材库。**

为 AI Agent 工作流而生:任务需要真实拍摄素材(而非 AI 生成)时,Agent 跑一下脚本,拿回 JSON,文件已经归到对应目录。

## 为什么

免费素材站很分散,而且不同网络环境下可达性不同。stock-fetch 刻意做小:

- **两个可用源,一条命令。** Pixabay(官方 API,免费 key)覆盖图片+视频;Mixkit(免 key,页面解析)覆盖视频+音乐+音效。
- **按类型归档。** 下载自动落 `assets/images | video | bgm | audio`,素材库不用手动整理。
- **许可证随结果输出。** 每条结果带许可证字段,引用时不用二次查。
- **零依赖。** 纯 Python 标准库,stdout 输出 JSON,退出码正常。

## 快速开始

```bash
# 只搜不下
python scripts/stock_fetch.py search -q "sunset ocean" --kind image -n 5

# 下载前 2 条视频
python scripts/stock_fetch.py get -q "city timelapse" --kind video -n 2

# 音乐和音效(免 key)
python scripts/stock_fetch.py get -q "upbeat corporate" --kind music -n 3
python scripts/stock_fetch.py get -q "click" --kind sfx -n 3
```

结果 JSON 示例:

```json
{
  "ok": true,
  "downloaded": 1,
  "failed": 0,
  "items": [
    {
      "source": "mixkit",
      "type": "video",
      "url": "https://assets.mixkit.co/videos/41576/41576-1080.mp4",
      "license": "Mixkit License (free for commercial use, no attribution)",
      "saved": "assets/video/mixkit_sunset_80676.mp4",
      "bytes": 187175135
    }
  ]
}
```

## 配置

| 配置项 | 方式 |
|---|---|
| Pixabay key | 在 [pixabay.com/api/docs](https://pixabay.com/api/docs/) 免费申请——`PIXABAY_API_KEY=xxx` 写进 `scripts/.env`,或导出环境变量 |
| 素材库根目录 | `STOCK_FETCH_ROOT` 环境变量,默认当前目录下 `./assets` |
| env 文件位置 | `STOCK_FETCH_ENV` 环境变量,默认脚本旁 `scripts/.env` |
| 落盘目录覆盖 | `--dest video/city`(相对素材库根目录) |

频率限制:Pixabay 允许 100 请求/60 秒,禁止系统性批量下载——本工具定位是"每个任务挑几条素材",不是镜像整库。

## 数据源

| 源 | 素材类型 | key | 说明 |
|---|---|---|---|
| [Pixabay](https://pixabay.com/) | 图片+视频 | 免费申请 | 官方 API,已开安全搜索 |
| [Mixkit](https://mixkit.co/) | 视频+音乐+音效 | 免 key | 搜索页解析;1080p 直链按固定命名规律推断 |
| [Wikimedia Commons](https://commons.wikimedia.org/) | CC/公有领域图片 | 免 key | `--source wikimedia` 兜底;保留署名 |

## 作为 Agent 技能使用

仓库含 `SKILL.md`,`npx skills add <本仓库>`(或任何读 SKILL.md 的技能加载器)可以直接暴露给你的 Agent。

## 许可证

Apache-2.0
