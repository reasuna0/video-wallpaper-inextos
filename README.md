
# 瑙嗛澹佺焊鎻掍欢 / Video Wallpaper Plugin

閽堝 iNextOS 杞矾鐢辩郴缁熺殑瑙嗛澹佺焊鎻掍欢锛屼负鐧诲綍椤甸潰璁剧疆鍔ㄦ€佽棰戣儗鏅€?
<img width="1891" height="933" alt="image" src="https://github.com/user-attachments/assets/1f1eddd8-cae7-4f4d-92ce-fad8fb18335e" />
<img width="1880" height="946" alt="image" src="https://github.com/user-attachments/assets/7427b855-567b-496c-81a2-51d27deac77b" />

Video wallpaper plugin for iNextOS / RoceOS router systems, sets a dynamic video background for the login page.

[![Version](https://img.shields.io/badge/version-v1.7-blue)](https://github.com/reasuna0/video-wallpaper-inextos/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-iNextOS%2FRoceOS-orange)]()

---

## 鍔熻兘鐗规€?/ Features

### 涓枃
- 鉁?**瀹炴椂鍒囨崲澹佺焊**锛氬湪绠＄悊椤甸潰鐐瑰嚮瑙嗛鍚庯紝鐧诲綍椤甸潰澹佺焊绔嬪嵆鑷姩鍒囨崲锛屾棤闇€鎵嬪姩鍒锋柊椤甸潰
- 鉁?**瑙嗛灏侀潰缂╃暐鍥?*锛氭瘡涓棰戣嚜鍔ㄧ敓鎴愮涓€甯ч瑙堝浘锛屼竴鐩簡鐒讹紙3绾跨▼骞跺彂鐢熸垚锛?
- 鉁?**鑷畾涔夎棰戠洰褰?*锛氭敮鎸佹祻瑙堝拰閫夋嫨浠绘剰鐩綍锛屽彲鏂板缓鏂囦欢澶?
- 鉁?**涓婁紶涓庤浆鐮?*锛歁P4/WebM/OGG 鐩存帴鎾斁锛屽叾浠栨牸寮忚嚜鍔ㄨ浆鐮侊紝甯﹁繘搴︽潯锛屽け璐ヨ嚜鍔ㄦ竻鐞?
- 鉁?**閫忔槑搴﹁皟鑺?*锛氭嫋鍔ㄦ粦鍧楀疄鏃惰皟鏁磋棰戦€忔槑搴?
- 鉁?**闈欓煶寮€鍏?*锛氫竴閿垏鎹㈣棰戝０闊?
- 鉁?**妗岄潰蹇嵎鏂瑰紡**锛氬畨瑁呭悗鑷姩鍦ㄧ郴缁熸闈㈠垱寤哄浘鏍?
- 鉁?**绯荤粺鏇存柊鑷剤**锛氱郴缁熸洿鏂板悗澹佺焊閰嶇疆鑷姩淇濈暀锛屾棤闇€閲嶆柊璁剧疆
- 鉁?**璺ㄥ煙鏀寔**锛欳ORS 澶村凡閰嶇疆锛岃矾鐢卞櫒涓婚〉闈㈠彲姝ｅ父璋冪敤 API

### English
- 鉁?**Live Wallpaper Switch**: Click a video in the manager, wallpaper changes instantly 鈥?no page refresh needed
- 鉁?**Video Thumbnails**: Auto-generates first-frame preview for each video (3-thread parallel)
- 鉁?**Custom Video Directory**: Browse and select any directory, create new folders
- 鉁?**Upload & Transcode**: MP4/WebM/OGG direct play; other formats auto-transcode with progress bar, auto-cleanup on failure
- 鉁?**Opacity Control**: Drag slider to adjust video opacity in real time
- 鉁?**Mute Toggle**: One-click switch for video audio
- 鉁?**Desktop Shortcut**: Auto-creates icon on system desktop after install
- 鉁?**Auto Recovery**: Wallpaper config persists after system updates
- 鉁?**CORS Support**: Cross-origin API calls from router main page work out of the box

---

## 瀹夎 / Installation

### 涓枃
1. 浠?[Releases](https://github.com/reasuna0/video-wallpaper-inextos/releases) 涓嬭浇鏈€鏂板畨瑁呭寘
2. 灏嗗畨瑁呭寘涓婁紶鍒拌蒋璺敱
3. 瑙ｅ帇骞跺畨瑁咃細
   ```bash
   tar -xzf video-wallpaper-v1.7.tar.gz
   cd video-wallpaper
   bash install.sh
   ```
4. 瀹夎瀹屾垚鍚庯紝妗岄潰浼氳嚜鍔ㄥ垱寤哄揩鎹锋柟寮?

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

## 浣跨敤 / Usage

### 璁块棶鍦板潃 / Access
- 绠＄悊椤甸潰 / Manager: `http://192.168.100.1:8686`
- 妗岄潰蹇嵎鏂瑰紡 / Desktop shortcut: 鑷姩鍒涘缓 / auto-created

### 鎿嶄綔姝ラ / Steps

| 鎿嶄綔 / Action | 璇存槑 / Description |
|---|---|
| 鍚敤澹佺焊 / Enable | 鐐瑰嚮 "Enable" 鎸夐挳寮€鍚棰戝绾?/ Click "Enable" to activate |
| 閫夋嫨瑙嗛 / Select Video | 鐐瑰嚮瑙嗛鍒楄〃涓殑浠绘剰瑙嗛锛屽绾稿疄鏃跺垏鎹?/ Click any video, wallpaper switches in real time |
| 璋冩暣閫忔槑搴?/ Opacity | 鎷栧姩 Opacity 婊戝潡 / Drag the Opacity slider |
| 闈欓煶寮€鍏?/ Mute | 鍕鹃€?鍙栨秷 Mute 澶嶉€夋 / Check/uncheck the Mute checkbox |
| 涓婁紶瑙嗛 / Upload | 鎷栨嫿鎴栫偣鍑讳笂浼犲尯鍩燂紝鏀寔鑷姩杞爜 / Drag & drop or click upload area |
| 鍒犻櫎瑙嗛 / Delete | 閫変腑瑙嗛鍚庣偣鍑?"Delete Selected" / Select video and click "Delete Selected" |
| 鑷畾涔夌洰褰?/ Custom Path | 鍦?Video Directory 涓慨鏀硅矾寰勶紝鏀寔娴忚鍜屾柊寤烘枃浠跺す / Modify path in Video Directory |

---

## 瑙嗛鐩綍 / Video Directory

- 榛樿鐩綍 / Default: `/opt/video-wallpaper/videos`
- 鍙嚜瀹氫箟涓轰换鎰忚矾寰?/ Customizable to any path (e.g., `/mnt/sata6-1/wallpapers`)
- 鏇存敼璺緞涓嶄細鍒犻櫎宸叉湁瑙嗛 / Changing path does not delete existing videos

---

## 鍗歌浇 / Uninstall

```bash
bash uninstall.sh
```

---

## 娉ㄦ剰浜嬮」 / Notes

- 棣栨瀹夎闇€瑕佹瀯寤?Docker 闀滃儚锛堢害 1-2 鍒嗛挓锛? First install builds a Docker image (~1-2 minutes)
- 瑙嗛鏂囦欢鏈€澶ф敮鎸?10GB / Max file size: 10GB
- 杞爜杩囩▼涓細鏄剧ず杩涘害鏉★紝澶辫触鑷姩鍒犻櫎鍘熸枃浠跺苟鎻愮ず / Transcoding shows progress bar; failed files are auto-deleted
- 绯荤粺鏇存柊鍚庡绾搁厤缃嚜鍔ㄤ繚鐣?/ Wallpaper config persists after system updates
- 閲嶆柊瀹夎鎴栨洿鏂板悗锛岄渶鍏?Disable 鍐?Enable 涓€娆″绾革紝璁╂柊鑴氭湰娉ㄥ叆 / After reinstall/update, Disable then Enable once to inject new scripts

---

## 鎶€鏈灦鏋?/ Architecture

```
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? Router Login Page (port 80)            鈹?
鈹? 鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹? 鈹?
鈹? 鈹? <video id="video-bg">            鈹? 鈹?
鈹? 鈹? Live update script (1s polling) 鈹? 鈹?
鈹? 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹? 鈹?
鈹?                   鈹?                   鈹?
鈹?                   鈻? fetch()           鈹?
鈹? Video Wallpaper Service (port 8686)    鈹?
鈹? 鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹? 鈹?
鈹? 鈹? Python HTTP Server               鈹? 鈹?
鈹? 鈹? - /api/status                    鈹? 鈹?
鈹? 鈹? - /api/select                    鈹? 鈹?
鈹? 鈹? - /api/thumb                     鈹? 鈹?
鈹? 鈹? - /api/upload                    鈹? 鈹?
鈹? 鈹? - Transcode worker (ffmpeg)      鈹? 鈹?
鈹? 鈹? - Thumbnail worker (3 threads)   鈹? 鈹?
鈹? 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹? 鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
```

---

## License

MIT
