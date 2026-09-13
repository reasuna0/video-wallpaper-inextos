#!/usr/bin/env python3
import os
import subprocess
import threading
import re
import time
import json
import shutil
import base64
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

WWW_DIR = "/opt/roceos/www"
INDEX_FILE = os.path.join(WWW_DIR, "index.html")
BACKUP_FILE = os.path.join(WWW_DIR, "index.html.bak")
DEFAULT_VIDEO_DIR = "/opt/video-wallpaper/videos"
APP_DIR = "/opt/video-wallpaper"
GLOBAL_CONFIG_FILE = os.path.join(APP_DIR, "config.json")

def get_video_dir():
    config = load_global_config()
    return config.get("video_dir", DEFAULT_VIDEO_DIR)

def load_global_config():
    if os.path.exists(GLOBAL_CONFIG_FILE):
        with open(GLOBAL_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"video_dir": DEFAULT_VIDEO_DIR}

def save_global_config(config):
    os.makedirs(APP_DIR, exist_ok=True)
    with open(GLOBAL_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_config_file():
    return os.path.join(get_video_dir(), ".video-wallpaper-config.json")
SYMLINK_NAME = "assets/wallpapers"
SYMLINK_PATH = os.path.join(WWW_DIR, SYMLINK_NAME)
PORT = 8686

VIDEO_BG_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="apple-touch-icon" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="RoceOS" />
    <title>RoceOS</title>
    <link rel="stylesheet" href="/winbox.css" />
    <script src="/winbox.js"></script>
    <script type="module" crossorigin src="/assets/index-Ck2AMJ6h.js"></script>
    <link rel="modulepreload" crossorigin href="/assets/vendor-lIaPRPpR.js">
    <link rel="modulepreload" crossorigin href="/assets/ui-B2U7SRGv.js">
    <link rel="stylesheet" crossorigin href="/assets/index-BTAVuU1g.css">
    <style>
      html, body {{ margin: 0; padding: 0; background: #000 !important; }}
      #video-bg {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; object-fit: cover; z-index: 0; opacity: {opacity}; pointer-events: none; }}
      #root {{ position: relative; z-index: 1; min-height: 100vh; background: transparent !important; }}
      #root > div {{ background: transparent !important; }}
      #root [style*="background-image"] {{ background-image: none !important; }}
      #root [class*="wallpaper"], #root [class*="background"], #root [class*="bg"] {{ background-image: none !important; background-color: transparent !important; }}
    </style>
  </head>
  <body>
    <video id="video-bg" src="/{symlink}/{video}" autoplay {muted} loop playsinline></video>
    <div id="root"></div>
  </body>
</html>"""


def load_config():
    config_file = get_config_file()
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    return {"enabled": False, "video": "", "opacity": 1.0, "muted": True}
def save_config(config):
    config_file = get_config_file()
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
def is_enabled():
    if not os.path.exists(INDEX_FILE):
        return False
    with open(INDEX_FILE, 'r') as f:
        return 'id="video-bg"' in f.read()


def get_thumb_dir():
    return os.path.join(get_video_dir(), ".thumbs")

def get_thumb_path(video_name):
    base = os.path.splitext(video_name)[0]
    return os.path.join(get_thumb_dir(), base + ".jpg")

def generate_thumbnail(video_name):
    """用 ffmpeg 提取视频第一帧作为缩略图（同步，供后台线程调用）"""
    video_path = os.path.join(get_video_dir(), video_name)
    thumb_path = get_thumb_path(video_name)
    if os.path.exists(thumb_path):
        return thumb_path
    os.makedirs(get_thumb_dir(), exist_ok=True)
    try:
        # -ss 放在 -i 前面，使用关键帧 seek，速度快很多
        subprocess.run(
            ['ffmpeg', '-y', '-ss', '00:00:01', '-i', video_path,
             '-vframes', '1', '-q:v', '4', '-vf', 'scale=240:-1',
             '-noaccurate_seek', thumb_path],
            capture_output=True, timeout=15
        )
        if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
            return thumb_path
    except:
        pass
    return None

# 缩略图生成队列（异步，多线程并发）
thumb_queue = []
thumb_workers = 0
MAX_THUMB_WORKERS = 3
thumb_lock = threading.Lock()

def thumb_worker():
    """后台线程：异步生成缩略图"""
    global thumb_workers
    while True:
        with thumb_lock:
            if not thumb_queue:
                thumb_workers -= 1
                return
            video_name = thumb_queue.pop(0)
        try:
            generate_thumbnail(video_name)
        except:
            pass

def queue_thumbnail(video_name):
    """将视频加入缩略图生成队列"""
    global thumb_workers
    thumb_path = get_thumb_path(video_name)
    if os.path.exists(thumb_path):
        return  # 已有缩略图，跳过
    with thumb_lock:
        if video_name not in thumb_queue:
            thumb_queue.append(video_name)
        # 如果工作线程数不足，启动新的
        if thumb_workers < MAX_THUMB_WORKERS:
            thumb_workers += 1
            t = threading.Thread(target=thumb_worker, daemon=True)
            t.start()

def list_videos():
    """列出视频，不阻塞生成缩略图（只检查是否已存在）"""
    if not os.path.exists(get_video_dir()):
        return []
    videos = []
    for f in os.listdir(get_video_dir()):
        if f.lower().endswith(('.mp4', '.webm', '.ogg')):
            path = os.path.join(get_video_dir(), f)
            thumb_path = get_thumb_path(f)
            if os.path.exists(thumb_path):
                thumb_url = "/api/thumb?video=" + f
            else:
                thumb_url = None
                queue_thumbnail(f)  # 后台异步生成
            videos.append({"name": f, "size": os.path.getsize(path), "thumb": thumb_url})
    return sorted(videos, key=lambda x: x["name"])



# 转码状态
transcode_state = {
    "running": False,
    "progress": 0,
    "filename": "",
    "error": None,
    "total_duration": 0
}

def ensure_symlink():
    if not os.path.exists(get_video_dir()):
        os.makedirs(get_video_dir(), exist_ok=True)
    assets_dir = os.path.join(WWW_DIR, "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir, exist_ok=True)
    target = get_video_dir()
    # 如果符号链接已存在但指向错误路径，删除重建
    if os.path.islink(SYMLINK_PATH):
        if os.readlink(SYMLINK_PATH) != target:
            os.unlink(SYMLINK_PATH)
            os.symlink(target, SYMLINK_PATH)
    elif os.path.exists(SYMLINK_PATH):
        shutil.rmtree(SYMLINK_PATH)
        os.symlink(target, SYMLINK_PATH)
    else:
        os.symlink(target, SYMLINK_PATH)


def enable_wallpaper(video=None, opacity=None, muted=None):
    config = load_config()
    if video:
        config["video"] = video
    if opacity is not None:
        config["opacity"] = opacity
    if muted is not None:
        config["muted"] = bool(muted)
    if not config.get("video") or not os.path.exists(os.path.join(get_video_dir(), config["video"])):
        videos = list_videos()
        if videos:
            config["video"] = videos[0]["name"]
        else:
            return False
    config["enabled"] = True
    save_config(config)

    # Get original index.html content
    if is_enabled():
        # Already modified, restore from backup
        if os.path.exists(BACKUP_FILE):
            with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                original = f.read()
        else:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                original = f.read()
    else:
        # Fresh original, back it up
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            original = f.read()
        shutil.copy2(INDEX_FILE, BACKUP_FILE)

    # Build CSS
    opacity_val = config.get("opacity", 1.0)
    css = f"""<style>
      html, body {{ margin: 0; padding: 0; background: #000 !important; }}
      #video-bg {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; object-fit: cover; z-index: 0; opacity: {opacity_val}; pointer-events: none; }}
      #root {{ position: relative; z-index: 1; min-height: 100vh; background: transparent !important; }}
      #root > div {{ background: transparent !important; }}
      #root [style*="background-image"] {{ background-image: none !important; }}
      #root [class*="wallpaper"], #root [class*="background"], #root [class*="bg"] {{ background-image: none !important; background-color: transparent !important; }}
    </style>"""

    # Build video tag + 实时轮询脚本
    muted_attr = "muted" if config.get("muted", True) else ""
    video_tag = f'<video id="video-bg" src="/{SYMLINK_NAME}/{config["video"]}" autoplay {muted_attr} loop playsinline></video>'
    # 实时更新脚本：每1秒轮询，视频变化时自动切换，无需刷新页面
    # 注意：必须用完整地址，因为壁纸页面在路由器主站(80端口)，而API在8686端口
    live_update_script = """<script>
(function() {
  var API_BASE = 'http://' + window.location.hostname + ':8686';
  setInterval(function() {
    fetch(API_BASE + '/api/status').then(function(r) { return r.json(); }).then(function(data) {
      if (data.enabled && data.video) {
        var newSrc = '/assets/wallpapers/' + data.video;
        var video = document.getElementById('video-bg');
        if (video && video.getAttribute('src') !== newSrc) {
          video.setAttribute('src', newSrc);
          video.load();
          video.play().catch(function(){});
        }
        if (data.opacity !== undefined) {
          video.style.opacity = data.opacity;
        }
        if (data.muted !== undefined) {
          video.muted = data.muted;
        }
      }
    }).catch(function(){});
  }, 1000);
})();
</script>"""

    # Inject CSS before </head>
    html = original.replace('</head>', css + '\n  </head>')
    # Inject video + live update script after <body>
    html = html.replace('<body>', '<body>\n    ' + video_tag + '\n    ' + live_update_script, 1)

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    return True


def disable_wallpaper():
    config = load_config()
    config["enabled"] = False
    save_config(config)
    if os.path.exists(BACKUP_FILE):
        shutil.copy2(BACKUP_FILE, INDEX_FILE)
        return True
    return False


def delete_video(video_name):
    """Delete a video file. If it's the current video, switch to another or disable."""
    filepath = os.path.join(get_video_dir(), os.path.basename(video_name))
    if not os.path.exists(filepath):
        return False, "Video not found"

    config = load_config()
    was_current = (config.get("video") == video_name)

    os.remove(filepath)
    # 同时删除缩略图
    thumb_path = get_thumb_path(video_name)
    if os.path.exists(thumb_path):
        try: os.remove(thumb_path)
        except: pass

    if was_current:
        videos = list_videos()
        if videos and is_enabled():
            config["video"] = videos[0]["name"]
            save_config(config)
            enable_wallpaper()
            return True, "Deleted and switched to: " + videos[0]["name"]
        elif is_enabled():
            disable_wallpaper()
            return True, "Deleted, wallpaper disabled (no videos left)"
        else:
            config["video"] = ""
            save_config(config)
            return True, "Deleted"
    return True, "Deleted: " + video_name


class Handler(BaseHTTPRequestHandler):
    def end_headers(self):
        # 添加 CORS 头，允许路由器主页面(80端口)跨域请求
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        # 处理 CORS 预检请求
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ('/', '/index.html'):
            self.send_html(FRONTEND)
        elif path == '/api/transcode-status':
            self.send_json({
                "running": transcode_state["running"],
                "progress": transcode_state["progress"],
                "filename": transcode_state["filename"],
                "error": transcode_state["error"]
            })
        elif path == '/api/status':
            config = load_config()
            self.send_json({
                "enabled": is_enabled(),
                "video": config.get("video", ""),
                "opacity": config.get("opacity", 1.0),
                "muted": config.get("muted", True),
                "video_dir": get_video_dir(),
                "videos": list_videos()
            })
        elif path == '/api/videos':
            self.send_json({"videos": list_videos()})
        elif path == '/api/thumb':
            from urllib.parse import parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            video_name = params.get('video', [''])[0]
            video_name = os.path.basename(video_name)
            if not video_name:
                self.send_json({"error": "no video"}, 400)
                return
            thumb_path = get_thumb_path(video_name)
            if os.path.exists(thumb_path):
                with open(thumb_path, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', len(data))
                self.send_header('Cache-Control', 'public, max-age=3600')
                self.end_headers()
                self.wfile.write(data)
            else:
                # 缩略图还没生成，加入队列后台生成，返回 404
                queue_thumbnail(video_name)
                self.send_json({"error": "no thumbnail"}, 404)
        else:
            self.send_json({"error": "not found"}, 404)


    def do_POST(self):
        path = urlparse(self.path).path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length else '{}'

        if path == '/api/enable':
            try:
                data = json.loads(body)
            except:
                data = {}
            video = data.get('video')
            opacity = data.get('opacity')
            muted = data.get('muted')
            if opacity is not None:
                try:
                    opacity = float(opacity)
                except:
                    opacity = None
            ensure_symlink()
            if is_enabled():
                # 已启用时只更新配置，靠实时更新脚本自动同步（更快）
                config = load_config()
                if video:
                    config["video"] = video
                if opacity is not None:
                    config["opacity"] = opacity
                if muted is not None:
                    config["muted"] = bool(muted)
                config["enabled"] = True
                save_config(config)
                self.send_json({"success": True, "message": "Updated"})
            else:
                ok = enable_wallpaper(video, opacity, muted)
                if ok:
                    self.send_json({"success": True, "message": "Enabled"})
                else:
                    self.send_json({"success": False, "message": "No video available"}, 400)

        elif path == '/api/disable':
            disable_wallpaper()
            self.send_json({"success": True, "message": "Disabled"})

        elif path == '/api/select':
            data = json.loads(body)
            video = data.get('video')
            if video and os.path.exists(os.path.join(get_video_dir(), video)):
                config = load_config()
                config["video"] = video
                save_config(config)
                # 已启用时不重写 index.html，靠实时更新脚本自动切换（更快）
                if not is_enabled():
                    enable_wallpaper()
                self.send_json({"success": True, "message": "Selected: " + video})
            else:
                self.send_json({"success": False, "message": "Not found"}, 400)

        elif path == '/api/delete':
            data = json.loads(body)
            video = data.get('video')
            if video:
                success, msg = delete_video(video)
                self.send_json({"success": success, "message": msg})
            else:
                self.send_json({"success": False, "message": "No video specified"}, 400)

        elif path == '/api/browse':
            try:
                data = json.loads(body)
            except:
                data = {}
            dir_path = data.get('path', '/')
            if not os.path.isabs(dir_path):
                dir_path = '/'
            if not os.path.exists(dir_path):
                self.send_json({"success": False, "message": "Directory not found"}, 404)
                return
            items = []
            parent = os.path.dirname(dir_path.rstrip('/'))
            if parent and parent != dir_path:
                items.append({"name": "..", "path": parent, "type": "dir"})
            try:
                names = os.listdir(dir_path)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, 400)
                return
            for name in names:
                try:
                    full_path = os.path.join(dir_path, name)
                    if os.path.isdir(full_path):
                        items.append({"name": name, "path": full_path, "type": "dir"})
                except Exception:
                    pass
            # Sort case-insensitive
            items[1:] = sorted(items[1:], key=lambda x: x["name"].lower())
            self.send_json({"success": True, "current": dir_path, "items": items})
            return

        elif path == '/api/mkdir':
            try:
                data = json.loads(body)
            except:
                data = {}
            parent = data.get('parent', '/')
            name = data.get('name', '').strip()
            if not name:
                self.send_json({"success": False, "message": "Folder name cannot be empty"}, 400)
                return
            if not os.path.isabs(parent):
                parent = '/'
            new_path = os.path.join(parent, name)
            if os.path.exists(new_path):
                self.send_json({"success": False, "message": "Already exists"}, 400)
                return
            try:
                os.makedirs(new_path, exist_ok=True)
                self.send_json({"success": True, "message": "Created: " + new_path, "path": new_path})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, 400)
            return


        elif path == '/api/setpath':
            try:
                data = json.loads(body)
            except:
                data = {}
            new_path = data.get('path', '').strip()
            if not new_path:
                self.send_json({"success": False, "message": "Path cannot be empty"}, 400)
                return
            if not os.path.isabs(new_path):
                self.send_json({"success": False, "message": "Must be absolute path"}, 400)
                return
            try:
                os.makedirs(new_path, exist_ok=True)
            except Exception as e:
                self.send_json({"success": False, "message": "Cannot create directory: " + str(e)}, 400)
                return
            test_file = os.path.join(new_path, ".write_test")
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                self.send_json({"success": False, "message": "Directory not writable: " + str(e)}, 400)
                return
            global_config = load_global_config()
            global_config["video_dir"] = new_path
            save_global_config(global_config)
            ensure_symlink()
            if is_enabled():
                enable_wallpaper()
            self.send_json({"success": True, "message": "Path updated to: " + new_path, "video_dir": new_path})

        elif path == '/api/upload':
            # 兼容旧的 base64 方式（小文件）
            try:
                data = json.loads(body)
                filename = data.get('filename', 'video.mp4')
                filedata = data.get('data', '')
                if filename and filedata:
                    filename = os.path.basename(filename)
                    filepath = os.path.join(get_video_dir(), filename)
                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(filedata))
                    self.send_json({"success": True, "message": "Uploaded: " + filename, "video": filename})
                else:
                    self.send_json({"success": False, "message": "Upload failed"}, 400)
            except Exception as e:
                self.send_json({"success": False, "message": "Upload failed: " + str(e)}, 400)

        else:
            self.send_json({"error": "not found"}, 404)
    def do_PUT(self):
        global transcode_state
        path = self.path.split('?')[0]
        if path == '/api/upload':
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                filename = params.get('filename', ['video.mp4'])[0]
                filename = os.path.basename(filename)
                allowed_ext = ('.mp4', '.webm', '.ogg', '.mkv', '.mov', '.avi',
                              '.flv', '.wmv', '.ts', '.m2ts', '.m4v', '.3gp', '.rmvb')
                if not filename.lower().endswith(allowed_ext):
                    self.send_json({"success": False, "message": "不支持的文件格式"}, 400)
                    return
                if transcode_state["running"]:
                    self.send_json({"success": False, "message": "已有转码任务进行中，请稍候"}, 400)
                    return
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self.send_json({"success": False, "message": "空文件"}, 400)
                    return
                filepath = os.path.join(get_video_dir(), filename)
                read = 0
                with open(filepath, 'wb') as f:
                    while read < content_length:
                        chunk_size = min(65536, content_length - read)
                        chunk = self.rfile.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        read += len(chunk)
                native_formats = ('.mp4', '.webm', '.ogg')
                if filename.lower().endswith(native_formats):
                    queue_thumbnail(filename)  # 后台异步生成缩略图
                    self.send_json({"success": True, "message": "上传完成: " + filename, "video": filename, "transcode": False})
                else:
                    base = os.path.splitext(filename)[0]
                    dst_path = os.path.join(get_video_dir(), base + '.mp4')
                    t = threading.Thread(target=run_transcode, args=(filepath, dst_path, filename), daemon=True)
                    t.start()
                    self.send_json({"success": True, "message": "上传完成，开始转码...", "video": filename, "transcode": True})
            except Exception as e:
                self.send_json({"success": False, "message": "上传失败: " + str(e)}, 500)
        else:
            self.send_json({"error": "not found"}, 404)

    def log_message(self, format, *args):
        pass


FRONTEND = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Video Wallpaper Manager</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: #fff; padding: 20px; }
.container { max-width: 800px; margin: 0 auto; }
h1 { text-align: center; margin-bottom: 30px; font-size: 28px; }
.card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 24px; margin-bottom: 20px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
.status { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.status-badge { padding: 6px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; }
.status-on { background: #4CAF50; }
.status-off { background: #666; }
.btn { padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: all 0.3s; font-weight: 600; }
.btn-primary { background: #4CAF50; color: #fff; }
.btn-primary:hover { background: #45a049; }
.btn-danger { background: #f44336; color: #fff; }
.btn-danger:hover { background: #da190b; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.video-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; margin-top: 16px; }
.video-item { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 12px; cursor: pointer; transition: all 0.3s; border: 2px solid transparent; }
.video-item:hover { background: rgba(255,255,255,0.1); transform: translateY(-2px); }
.video-item.active { border-color: #4CAF50; background: rgba(76,175,80,0.1); }
.video-thumb { width: 100%; height: 124px; object-fit: cover; border-radius: 8px; margin-bottom: 10px; background: #222; }
.video-thumb-placeholder { width: 100%; height: 124px; border-radius: 8px; margin-bottom: 10px; background: #222; display: flex; align-items: center; justify-content: center; color: #555; font-size: 12px; }
.video-name { font-size: 13px; margin-bottom: 6px; word-break: break-all; line-height: 1.4; }
.video-size { font-size: 12px; color: #aaa; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-header h3 { margin: 0; }
.upload-area { border: 2px dashed rgba(255,255,255,0.3); border-radius: 12px; padding: 40px; text-align: center; cursor: pointer; transition: all 0.3s; }
.upload-area:hover { border-color: #4CAF50; background: rgba(76,175,80,0.05); }
.upload-area.dragover { border-color: #4CAF50; background: rgba(76,175,80,0.1); }
.slider-container { margin: 16px 0; }
.slider-container label { display: block; margin-bottom: 8px; font-size: 14px; color: #aaa; }
input[type="range"] { width: 100%; }
.toast { position: fixed; top: 20px; right: 20px; padding: 16px 24px; border-radius: 8px; color: #fff; font-weight: 600; z-index: 1000; animation: slideIn 0.3s; }
.toast-success { background: #4CAF50; }
.toast-error { background: #f44336; }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
.current-video { margin-top: 12px; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px; font-size: 14px; }
.modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 2000; }
.modal-content { background: #1a1a2e; padding: 30px; border-radius: 16px; max-width: 400px; text-align: center; border: 1px solid rgba(255,255,255,0.1); }
.modal-content h3 { margin-bottom: 16px; }
.modal-content p { color: #aaa; margin-bottom: 24px; word-break: break-all; }
.modal-buttons { display: flex; gap: 12px; justify-content: center; }
</style>
</head>
<body>
<div class="container">
  <h1>Video Wallpaper Manager</h1>
  <div class="card">
    <div class="status">
      <span>Status</span>
      <span id="statusBadge" class="status-badge status-off">Disabled</span>
    </div>
    <div id="currentVideo" class="current-video" style="display:none;"></div>
    <div style="display:flex; gap:12px; margin-top:16px;">
      <button id="enableBtn" class="btn btn-primary">Enable</button>
      <button id="disableBtn" class="btn btn-danger" disabled>Disable</button>
    </div>
    <div class="slider-container">
      <label>Opacity: <span id="opacityValue">100%</span></label>
      <input type="range" id="opacitySlider" min="0.1" max="1" step="0.05" value="1">
    </div>
    <div style="display:flex; align-items:center; gap:8px; margin-top:8px;">
      <input type="checkbox" id="mutedCheckbox" checked style="width:18px; height:18px; cursor:pointer;">
      <label for="mutedCheckbox" style="font-size:14px; color:#aaa; cursor:pointer;">Mute (no sound)</label>
    </div>
  </div>
  <div class="card">
    <div class="card-header">
      <h3>Video Directory</h3>
    </div>
    <div style="display:flex; gap:8px; margin-bottom:8px;">
      <input type="text" id="pathInput" style="flex:1; padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.2); background:rgba(0,0,0,0.3); color:#fff; font-size:14px;" placeholder="/opt/video-wallpaper/videos">
      <button id="browsePathBtn" class="btn btn-sm" style="background:#2196F3; color:#fff;">Browse</button>
      <button id="savePathBtn" class="btn btn-primary btn-sm">Save</button>
    </div>
    <button id="resetPathBtn" class="btn btn-sm" style="background:#666; color:#fff;">Reset to Default</button>
    <p style="font-size:12px; color:#aaa; margin-top:8px;">Changing path will not delete existing videos. Symlink will be updated automatically.</p>
  </div>
  <div class="card">
    <div class="card-header">
      <h3>Videos</h3>
      <button id="deleteCurrentBtn" class="btn btn-danger btn-sm" disabled>Delete Selected</button>
    </div>
    <div id="videoList" class="video-list"></div>
  </div>
  <div class="card">
    <h3 style="margin-bottom:16px;">Upload</h3>
    <div id="uploadArea" class="upload-area">
      <p>点击或拖拽视频文件到此处上传</p>
      <p style="font-size:12px; color:#aaa; margin-top:8px;">支持 MP4/WebM/OGG 直接播放，MKV/MOV/AVI/FLV 等格式自动转码</p>
    </div>
    <input type="file" id="fileInput" accept="video/*" style="display:none;">
    <div id="transcodeProgress" style="display:none; margin-top:16px;">
      <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
        <span id="transcodeFilename" style="font-size:14px;">转码中...</span>
        <span id="transcodePercent" style="font-size:14px; font-weight:bold;">0%</span>
      </div>
      <div style="width:100%; height:8px; background:#333; border-radius:4px; overflow:hidden;">
        <div id="transcodeBar" style="height:100%; width:0%; background:linear-gradient(90deg,#4CAF50,#8BC34A); transition:width 0.3s;"></div>
      </div>
    </div>
  </div>
</div>
<div id="deleteModal" class="modal" style="display:none;">
  <div class="modal-content">
    <h3>Confirm Delete</h3>
    <p id="deleteModalText">Are you sure?</p>
    <div class="modal-buttons">
      <button id="cancelDelete" class="btn btn-primary">Cancel</button>
      <button id="confirmDelete" class="btn btn-danger">Delete</button>
    </div>
  </div>
</div>
<div id="browseModal" class="modal" style="display:none;">
  <div class="modal-content" style="max-width:500px; text-align:left;">
    <h3 style="margin-bottom:16px;">Select Directory</h3>
    <div id="browseCurrent" style="font-size:13px; color:#aaa; margin-bottom:12px; word-break:break-all;">/</div>
    <div id="browseList" style="max-height:300px; overflow-y:auto; background:rgba(0,0,0,0.2); border-radius:8px; padding:8px; margin-bottom:16px;"></div>
    <div style="display:flex; gap:8px; margin-bottom:12px;">
      <input type="text" id="newFolderInput" style="flex:1; padding:8px; border-radius:6px; border:1px solid rgba(255,255,255,0.2); background:rgba(0,0,0,0.3); color:#fff; font-size:13px;" placeholder="New folder name...">
      <button id="newFolderBtn" class="btn btn-sm" style="background:#FF9800; color:#fff;">New Folder</button>
    </div>
    <div class="modal-buttons">
      <button id="cancelBrowse" class="btn btn-sm" style="background:#666; color:#fff;">Cancel</button>
      <button id="selectBrowse" class="btn btn-primary btn-sm">Select This Dir</button>
    </div>
  </div>
</div>
<script>
async function api(url, options) {
  const res = await fetch(url, options || {});
  return res.json();
}
function showToast(msg, type) {
  const toast = document.createElement('div');
  toast.className = 'toast toast-' + (type || 'success');
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes/1024).toFixed(1) + ' KB';
  return (bytes/1048576).toFixed(1) + ' MB';
}
let currentSelectedVideo = '';
async function loadStatus() {
  const data = await api('/api/status');
  const badge = document.getElementById('statusBadge');
  const enableBtn = document.getElementById('enableBtn');
  const disableBtn = document.getElementById('disableBtn');
  const currentVideo = document.getElementById('currentVideo');
  const opacitySlider = document.getElementById('opacitySlider');
  const opacityValue = document.getElementById('opacityValue');
  if (data.enabled) {
    badge.textContent = 'Enabled';
    badge.className = 'status-badge status-on';
    enableBtn.disabled = true;
    disableBtn.disabled = false;
    currentVideo.style.display = 'block';
    currentVideo.textContent = 'Current: ' + data.video;
  } else {
    badge.textContent = 'Disabled';
    badge.className = 'status-badge status-off';
    enableBtn.disabled = false;
    disableBtn.disabled = true;
    currentVideo.style.display = 'none';
  }
  opacitySlider.value = data.opacity || 1;
  opacityValue.textContent = Math.round((data.opacity || 1) * 100) + '%';
  document.getElementById('mutedCheckbox').checked = data.muted !== false;
  const list = document.getElementById('videoList');
  list.innerHTML = '';
  if (data.videos.length === 0) {
    list.innerHTML = '<p style="color:#aaa; grid-column: 1/-1; text-align:center; padding:20px;">No videos. Upload one below.</p>';
    return;
  }
  data.videos.forEach(v => {
    const item = document.createElement('div');
    item.className = 'video-item' + (v.name === data.video ? ' active' : '');
    const thumbHtml = v.thumb
      ? `<img class="video-thumb" src="${v.thumb}" alt="${v.name}" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
         <div class="video-thumb-placeholder" style="display:none;">生成中...</div>`
      : '<div class="video-thumb-placeholder">生成中...</div>';
    item.innerHTML = `
      ${thumbHtml}
      <div class="video-name">${v.name}</div>
      <div class="video-size">${formatSize(v.size)}</div>
    `;
    item.onclick = () => selectVideo(v.name);
    list.appendChild(item);
  });
  // Enable/disable delete button
  currentSelectedVideo = data.video || '';
  const deleteBtn = document.getElementById('deleteCurrentBtn');
  deleteBtn.disabled = !data.video || data.videos.length === 0;
  if (data.video_dir) {
    document.getElementById('pathInput').value = data.video_dir;
  }
  // 如果还有视频没有缩略图，5秒后自动刷新（后台生成中）
  const missingThumbs = data.videos.filter(v => !v.thumb).length;
  if (missingThumbs > 0) {
    setTimeout(loadStatus, 5000);
  }
}

document.getElementById('savePathBtn').onclick = async function() {
  const path = document.getElementById('pathInput').value.trim();
  if (!path) { showToast('Path cannot be empty', 'error'); return; }
  const res = await api('/api/setpath', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({path: path})});
  showToast(res.message, res.success ? 'success' : 'error');
  if (res.success) loadStatus();
};
document.getElementById('resetPathBtn').onclick = async function() {
  document.getElementById('pathInput').value = '/opt/video-wallpaper/videos';
  const res = await api('/api/setpath', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({path: '/opt/video-wallpaper/videos'})});
  showToast(res.message, res.success ? 'success' : 'error');
  if (res.success) loadStatus();
};
function showDeleteModal() {
  if (!currentSelectedVideo) return;
  document.getElementById('deleteModalText').textContent = 'Delete "' + currentSelectedVideo + '"? This cannot be undone.';
  document.getElementById('deleteModal').style.display = 'flex';
}
document.getElementById('deleteCurrentBtn').onclick = showDeleteModal;
document.getElementById('cancelDelete').onclick = () => {
  document.getElementById('deleteModal').style.display = 'none';
};
document.getElementById('confirmDelete').onclick = async () => {
  if (!currentSelectedVideo) return;
  const res = await api('/api/delete', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({video: currentSelectedVideo})
  });
  showToast(res.message, res.success ? 'success' : 'error');
  document.getElementById('deleteModal').style.display = 'none';
  loadStatus();
};
document.getElementById('enableBtn').onclick = async () => {
  const opacity = parseFloat(document.getElementById('opacitySlider').value);
  const muted = document.getElementById('mutedCheckbox').checked;
  const res = await api('/api/enable', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({opacity, muted})});
  showToast(res.message, res.success ? 'success' : 'error');
  loadStatus();
};
document.getElementById('mutedCheckbox').onchange = async () => {
  const badge = document.getElementById('statusBadge');
  if (badge.textContent === 'Enabled') {
    const opacity = parseFloat(document.getElementById('opacitySlider').value);
    const muted = document.getElementById('mutedCheckbox').checked;
    await api('/api/enable', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({opacity, muted})});
    showToast(muted ? 'Muted' : 'Sound on');
  }
};
document.getElementById('disableBtn').onclick = async () => {
  const res = await api('/api/disable', {method:'POST'});
  showToast(res.message);
  loadStatus();
};
document.getElementById('opacitySlider').oninput = (e) => {
  document.getElementById('opacityValue').textContent = Math.round(e.target.value * 100) + '%';
};
async function selectVideo(name) {
  const res = await api('/api/select', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({video: name})});
  showToast(res.message);
  loadStatus();
}
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
uploadArea.onclick = () => fileInput.click();
uploadArea.ondragover = (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); };
uploadArea.ondragleave = () => uploadArea.classList.remove('dragover');
uploadArea.ondrop = (e) => {
  e.preventDefault();
  uploadArea.classList.remove('dragover');
  if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
};
fileInput.onchange = (e) => { if (e.target.files.length) uploadFile(e.target.files[0]); };
let transcodePollTimer = null;
async function uploadFile(file) {
  if (file.size > 10 * 1024 * 1024 * 1024) {
    showToast('文件太大，最大支持 10GB', 'error');
    return;
  }
  showToast('上传中...');
  try {
    const res = await fetch('/api/upload?filename=' + encodeURIComponent(file.name), {
      method: 'PUT',
      body: file
    });
    const data = await res.json();
    if (!data.success) {
      showToast(data.message, 'error');
      return;
    }
    if (data.transcode) {
      // 显示进度条，开始轮询
      document.getElementById('transcodeProgress').style.display = 'block';
      document.getElementById('transcodeFilename').textContent = '转码中: ' + data.video;
      document.getElementById('transcodePercent').textContent = '0%';
      document.getElementById('transcodeBar').style.width = '0%';
      showToast('上传完成，开始转码...', 'success');
      pollTranscode();
    } else {
      showToast(data.message, 'success');
      loadStatus();
    }
  } catch(e) {
    showToast('上传失败: ' + e.message, 'error');
  }
}
function pollTranscode() {
  if (transcodePollTimer) clearInterval(transcodePollTimer);
  transcodePollTimer = setInterval(async () => {
    try {
      const res = await fetch('/api/transcode-status');
      const data = await res.json();
      document.getElementById('transcodePercent').textContent = data.progress + '%';
      document.getElementById('transcodeBar').style.width = data.progress + '%';
      if (data.error) {
        clearInterval(transcodePollTimer);
        transcodePollTimer = null;
        showToast('转码失败: ' + data.error + '，原文件已删除', 'error');
        document.getElementById('transcodeProgress').style.display = 'none';
        loadStatus();
      } else if (!data.running && data.progress >= 100) {
        clearInterval(transcodePollTimer);
        transcodePollTimer = null;
        showToast('转码完成', 'success');
        document.getElementById('transcodeProgress').style.display = 'none';
        loadStatus();
      }
    } catch(e) {}
  }, 500);
}
// Directory browser
let browseCurrentPath = '/';
async function browseDir(path) {
  const res = await api('/api/browse', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({path: path})});
  if (!res.success) { showToast(res.message, 'error'); return; }
  browseCurrentPath = res.current;
  document.getElementById('browseCurrent').textContent = res.current;
  const list = document.getElementById('browseList');
  list.innerHTML = '';
  res.items.forEach(function(item) {
    const div = document.createElement('div');
    div.style.cssText = 'padding:8px 12px; cursor:pointer; border-radius:6px; display:flex; align-items:center; gap:8px;';
    div.onmouseover = function() { div.style.background = 'rgba(255,255,255,0.1)'; };
    div.onmouseout = function() { div.style.background = 'transparent'; };
    const icon = item.name === '..' ? '..' : '[DIR]';
    div.innerHTML = '<span style="font-size:14px; color:#4CAF50; min-width:50px;">' + icon + '</span><span style="font-size:14px;">' + item.name + '</span>';
    div.onclick = function() { browseDir(item.path); };
    list.appendChild(div);
  });
}
document.getElementById('browsePathBtn').onclick = function() {
  const current = document.getElementById('pathInput').value || '/';
  browseDir(current);
  document.getElementById('browseModal').style.display = 'flex';
};
document.getElementById('cancelBrowse').onclick = function() {
  document.getElementById('browseModal').style.display = 'none';
};
document.getElementById('selectBrowse').onclick = function() {
  document.getElementById('pathInput').value = browseCurrentPath;
  document.getElementById('browseModal').style.display = 'none';
  showToast('Path selected: ' + browseCurrentPath);
};
document.getElementById('newFolderBtn').onclick = async function() {
  const name = document.getElementById('newFolderInput').value.trim();
  if (!name) { showToast('Enter folder name', 'error'); return; }
  const res = await api('/api/mkdir', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({parent: browseCurrentPath, name: name})});
  showToast(res.message, res.success ? 'success' : 'error');
  if (res.success) {
    document.getElementById('newFolderInput').value = '';
    browseDir(browseCurrentPath);
  }
};
document.getElementById('newFolderInput').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') document.getElementById('newFolderBtn').click();
});
loadStatus();
</script>
</body>
</html>"""






def get_video_duration(filepath):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', filepath],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except:
        return 0

def run_transcode(src_path, dst_path, filename):
    global transcode_state
    try:
        transcode_state["running"] = True
        transcode_state["progress"] = 0
        transcode_state["filename"] = filename
        transcode_state["error"] = None
        total = get_video_duration(src_path)
        transcode_state["total_duration"] = total
        cmd = [
            'ffmpeg', '-y', '-i', src_path,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            dst_path
        ]
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        for line in proc.stderr:
            match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
            if match and total > 0:
                h, m, s = int(match.group(1)), int(match.group(2)), float(match.group(3))
                current = h * 3600 + m * 60 + s
                transcode_state["progress"] = min(99, int(current / total * 100))
        proc.wait()
        if proc.returncode == 0 and os.path.exists(dst_path):
            os.remove(src_path)
            transcode_state["progress"] = 100
            transcode_state["running"] = False
            # 转码完成后生成缩略图
            base = os.path.splitext(filename)[0]
            queue_thumbnail(base + '.mp4')
            time.sleep(2)
            transcode_state["filename"] = ""
        else:
            raise Exception(f"ffmpeg exit code {proc.returncode}")
    except Exception as e:
        transcode_state["running"] = False
        transcode_state["error"] = str(e)
        if os.path.exists(src_path):
            try: os.remove(src_path)
            except: pass
        if os.path.exists(dst_path):
            try: os.remove(dst_path)
            except: pass
        time.sleep(5)
        transcode_state["filename"] = ""
        transcode_state["error"] = None

def register_app_icon():
    """Register app icon in iNextOS dashboard"""
    db_path = "/opt/roceos/data/roceos.db"
    if not os.path.exists(db_path):
        return
    try:
        db = sqlite3.connect(db_path)
        cursor = db.cursor()
        cursor.execute("SELECT id FROM installed_apps WHERE app_id='video-wallpaper'")
        if cursor.fetchone():
            cursor.execute("""
                UPDATE installed_apps SET status='running', updated_at=datetime('now')
                WHERE app_id='video-wallpaper'
            """)
        else:
            cursor.execute("""
                INSERT INTO installed_apps
                (user_id, app_id, app_type, name, icon_url, version, status, config,
                 window_type, webapp_port, webapp_url, created_at, updated_at)
                VALUES (1, 'video-wallpaper', 'system', 'Video Wallpaper',
                        'https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/jellyfin.png',
                        '1.6', 'running', '{}', 'newWindow', 8686, '/',
                        datetime('now'), datetime('now'))
            """)
        db.commit()
        db.close()
    except Exception as e:
        print("Failed to register app icon:", e)


def main():
    ensure_symlink()
    register_app_icon()
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print("Video Wallpaper Manager started on port " + str(PORT))
    server.serve_forever()


if __name__ == '__main__':
    main()
