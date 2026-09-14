
# 视频壁纸插件 / Video Wallpaper Plugin

针对 iNextOS 软路由系统的视频壁纸插件，为web页面设置动态视频背景。
<img width="1891" height="933" alt="image" src="https://github.com/user-attachments/assets/1f1eddd8-cae7-4f4d-92ce-fad8fb18335e" />
<img width="1880" height="946" alt="image" src="https://github.com/user-attachments/assets/7427b855-567b-496c-81a2-51d27deac77b" />

Video wallpaper plugin for iNextOS / RoceOS router systems, sets a dynamic video background for the login page.

[![Version](https://img.shields.io/badge/version-v1.7-blue)](https://github.com/reasuna0/video-wallpaper-inextos/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-iNextOS%2FRoceOS-orange)]()

---

## 功能特性 / Features

### 中文
- ✅ **实时切换壁纸**：在管理页面点击视频后，web页面壁纸立即自动切换，无需手动刷新页面
- ✅ **视频封面缩略图**：每个视频自动生成第一帧预览图，一目了然（3线程并发生成）
- ✅ **自定义视频目录**：支持浏览和选择任意目录，可新建文件夹
- ✅ **上传与转码**：MP4/WebM/OGG 直接播放，其他格式自动转码，带进度条，失败自动清理
- ✅ **透明度调节**：拖动滑块实时调整视频透明度
- ✅ **静音开关**：一键切换视频声音
- ✅ **桌面快捷方式**：安装后自动在系统桌面创建图标
- ✅ **系统更新自愈**：系统更新后壁纸配置自动保留，无需重新设置
- ✅ **跨域支持**：CORS 头已配置，路由器主页面可正常调用 API

### English
- ✅ **Live Wallpaper Switch**: Click a video in the manager, wallpaper changes instantly — no page refresh needed
- ✅ **Video Thumbnails**: Auto-generates first-frame preview for each video (3-thread parallel)
- ✅ **Custom Video Directory**: Browse and select any directory, create new folders
- ✅ **Upload & Transcode**: MP4/WebM/OGG direct play; other formats auto-transcode with progress bar, auto-cleanup on failure
- ✅ **Opacity Control**: Drag slider to adjust video opacity in real time
- ✅ **Mute Toggle**: One-click switch for video audio
- ✅ **Desktop Shortcut**: Auto-creates icon on system desktop after install
- ✅ **Auto Recovery**: Wallpaper config persists after system updates
- ✅ **CORS Support**: Cross-origin API calls from router main page work out of the box

---

## 安装 / Installation

### 中文
1. 从 [Releases](https://github.com/reasuna0/video-wallpaper-inextos/releases) 下载最新安装包
2. 将安装包上传到软路由
3. 解压并安装：
   ```bash
   tar -xzf video-wallpaper-v1.7.tar.gz
   cd video-wallpaper
   bash install.sh
   ```
4. 安装完成后，桌面会自动创建快捷方式

### English
1. Download the latest package from [Releases](https://github.com/reasuna0/video-wallpaper-inextos/releases)
2. Upload the package to your router
3. Extract and install:
   ```bash
   tar -xzf video-wallpaper-v1.7.tar.gz
   cd video-wallpaper
   bash install.sh
   ```
4. A desktop shortcut is created automatically

---

## 使用 / Usage

### 访问地址 / Access
- 管理页面 / Manager: `http://192.168.100.1:8686`
- 桌面快捷方式 / Desktop shortcut: 自动创建 / auto-created

### 操作步骤 / Steps

| 操作 / Action | 说明 / Description |
|---|---|
| 启用壁纸 / Enable | 点击 "Enable" 按钮开启视频壁纸 / Click "Enable" to activate |
| 选择视频 / Select Video | 点击视频列表中的任意视频，壁纸实时切换 / Click any video, wallpaper switches in real time |
| 调整透明度 / Opacity | 拖动 Opacity 滑块 / Drag the Opacity slider |
| 静音开关 / Mute | 勾选/取消 Mute 复选框 / Check/uncheck the Mute checkbox |
| 上传视频 / Upload | 拖拽或点击上传区域，支持自动转码 / Drag & drop or click upload area |
| 删除视频 / Delete | 选中视频后点击 "Delete Selected" / Select video and click "Delete Selected" |
| 自定义目录 / Custom Path | 在 Video Directory 中修改路径，支持浏览和新建文件夹 / Modify path in Video Directory |

---

## 视频目录 / Video Directory

- 默认目录 / Default: `/opt/video-wallpaper/videos`
- 可自定义为任意路径 / Customizable to any path (e.g., `/mnt/sata6-1/wallpapers`)
- 更改路径不会删除已有视频 / Changing path does not delete existing videos

---

## 卸载 / Uninstall

```bash
bash uninstall.sh
```

---

## 注意事项 / Notes

- 首次安装需要构建 Docker 镜像（约 1-2 分钟）/ First install builds a Docker image (~1-2 minutes)
- 视频文件最大支持 10GB / Max file size: 10GB
- 转码过程中会显示进度条，失败自动删除原文件并提示 / Transcoding shows progress bar; failed files are auto-deleted
- 系统更新后壁纸配置自动保留 / Wallpaper config persists after system updates
- 重新安装或更新后，需先 Disable 再 Enable 一次壁纸，让新脚本注入 / After reinstall/update, Disable then Enable once to inject new scripts

---

## 技术架构 / Architecture

```
┌─────────────────────────────────────────┐
│  Router Login Page (port 80)            │
│  ┌───────────────────────────────────┐  │
│  │  <video id="video-bg">            │  │
│  │  Live update script (1s polling) │  │
│  └───────────────────────────────────┘  │
│                    │                    │
│                    ▼  fetch()           │
│  Video Wallpaper Service (port 8686)    │
│  ┌───────────────────────────────────┐  │
│  │  Python HTTP Server               │  │
│  │  - /api/status                    │  │
│  │  - /api/select                    │  │
│  │  - /api/thumb                     │  │
│  │  - /api/upload                    │  │
│  │  - Transcode worker (ffmpeg)      │  │
│  │  - Thumbnail worker (3 threads)   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## License

MIT
