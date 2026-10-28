---
name: yt-dlp
description: 使用 yt-dlp 下载视频、播放列表、音频和字幕，并查询可用格式。用户给出 YouTube、B站、X、TikTok、Vimeo 等视频链接并要求下载、提取音频、查看画质或排查下载问题时使用；只讨论视频内容、只读取在线字幕且不需要保存媒体时不要触发。
---

# yt-dlp 视频下载

只在用户明确要求下载、保存或提取媒体时执行。消息中出现视频链接不代表授权下载，不要自动抓取。

默认输出到 `~/Downloads/yt-dlp`，文件名包含视频 ID 以避免覆盖。默认只处理单条视频；用户明确要求播放列表或合集时才加 `--playlist`。

只处理用户有权保存的内容，并遵守网站条款。不要尝试绕过 DRM、付费墙或访问控制；浏览器 Cookie 仅用于用户明确授权且已有登录态的会话，不读取或输出 Cookie 内容。

## 前置检查

运行前检查：

```bash
yt-dlp --version
ffmpeg -version
```

如果缺少依赖，停止并报告安装要求，不要自动安装或修改全局环境。普通视频下载需要 `ffmpeg` 合并音视频；音频提取也需要 `ffmpeg`。

## 使用脚本

在本 Skill 目录运行：

```bash
python3 scripts/download.py "VIDEO_URL"
python3 scripts/download.py "VIDEO_URL" --list-formats
python3 scripts/download.py "VIDEO_URL" --max-height 1080
python3 scripts/download.py "VIDEO_URL" --audio
python3 scripts/download.py "VIDEO_URL" --subtitles
python3 scripts/download.py "PLAYLIST_URL" --playlist
python3 scripts/download.py "VIDEO_URL" --cookies chrome
```

- `--list-formats` 只列出格式，不下载。
- `--info` 只输出单条视频或播放列表的 JSON 信息，不下载。
- `--max-height` 限制最大分辨率，例如 `1080`、`720`。
- `--output` 修改输出目录。
- `--sub-langs` 修改字幕语言，默认 `zh.*,en.*`。
- `--playlist-items` 仅与 `--playlist` 一起使用，例如 `1:10`。
- `--cookies` 接受 yt-dlp 支持的浏览器名；非必要不要启用。

脚本会打印实际执行的命令但不展开 Cookie 内容。不要为了“保险”默认加 Cookie；先尝试普通下载，遇到登录、年龄验证或站点要求的明确错误时，再向用户说明原因并请求授权。

## 平台差异

遇到 YouTube 高画质、B站合集、Instagram 登录、代理或格式选择问题时，读取 [references/platform-tips.md](references/platform-tips.md)。这些是针对性排查说明，不是默认参数。

## 结果处理

下载完成后报告媒体标题、文件路径、实际格式和失败项。若只完成部分文件或 yt-dlp 返回非零状态，明确说明部分成功，不把退出码只因已有文件跳过视为全部成功。
