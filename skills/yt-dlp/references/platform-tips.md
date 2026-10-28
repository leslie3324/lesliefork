# 平台差异与故障排查

只在对应的下载失败或用户明确指定需要时使用本页参数。

## YouTube

高分辨率视频通常把视频流和音频流分开，必须由 `ffmpeg` 合并。出现登录、年龄验证或站点要求时，先确认浏览器中已有授权会话，再使用：

```bash
python3 scripts/download.py "VIDEO_URL" --cookies chrome
```

支持的浏览器名由当前 yt-dlp 版本决定。Cookie 是敏感登录材料，不要复制、打印或发送到外部服务。

如果公开视频的可用格式明显少于浏览器，通常是站点端访问策略变化。先确认 yt-dlp 版本，必要时再评估 PO Token 插件；不要仅因画质不足默认读取 Cookie。

## B站

普通视频使用默认命令。合集或分P需要用户明确授权后使用：

```bash
python3 scripts/download.py "SERIES_URL" --playlist --playlist-items 1:10
```

高画质可能依赖登录态。只在用户要求并授权后使用 `--cookies`。

## X、TikTok、Instagram

- X/TikTok 的公开内容通常无需登录，先直接下载。
- Instagram 多数内容需要登录态；失败时说明原因，用户授权后再尝试浏览器 Cookie。
- 不要承诺去除平台水印或突破访问限制，以下载工具当前返回的公开媒体为准。

## Twitch 与 Vimeo

- Twitch 点播和剪辑可以直接下载；正在直播的内容会持续占用网络和磁盘，开始前说明停止条件。
- Vimeo 的密码保护内容需要用户提供密码。不要在命令历史之外泄露密码，也不要把密码写入 Skill 或日志。

## 网络与代理

网络不可达时先区分 DNS、代理和站点拒绝。需要代理时直接把 yt-dlp 的 `--proxy` 参数交给命令行，不要修改全局代理配置。中国网络环境下可测试：

```bash
yt-dlp --proxy socks5://127.0.0.1:1080 "VIDEO_URL"
```

不要假设代理地址有效，也不要未经授权启动代理服务。

## 常见错误

| 现象 | 优先检查 |
|---|---|
| `yt-dlp: command not found` | 安装 yt-dlp；不要由 Skill 自动安装 |
| `ffmpeg not found` | 安装 ffmpeg；音视频合并和音频提取会失败 |
| `Requested format is not available` | 先用 `--list-formats` 查看当前站点实际提供的格式 |
| `Sign in required` / 年龄验证 | 确认登录态并取得 Cookie 授权，或停止 |
| 网络中断 | 检查代理和连接；重试前确认已下载的 `.part` 文件是否可续传 |
| 下载速度过慢 | 可评估 `--concurrent-fragments 3`，不要盲目提高并发 |

不要把网页解析失败等同于视频不存在，也不要把 DRM 错误描述成可以通过切换格式解决。
