#!/bin/bash
set -e
APP_DIR="/opt/video-wallpaper"
COMPOSE_DIR="/opt/roceos/apps/video-wallpaper"
PORT=8686

echo "=== Video Wallpaper v1.7.2 Installer ==="

# 鍒涘缓鐩綍
mkdir -p "$APP_DIR/videos"
mkdir -p "$COMPOSE_DIR"

# 澶嶅埗鏂囦欢
cp server.py "$APP_DIR/server.py"
chmod +x "$APP_DIR/server.py"
cp docker-compose.yml "$COMPOSE_DIR/docker-compose.yml"
cp Dockerfile "$COMPOSE_DIR/Dockerfile"

# 鍒濆鍖栭厤缃?
if [ ! -f "$APP_DIR/config.json" ]; then
    echo '{"video_dir": "/opt/video-wallpaper/videos"}' > "$APP_DIR/config.json"
fi

# 鍋滄鏃у鍣?
docker stop video-wallpaper 2>/dev/null || true
docker rm video-wallpaper 2>/dev/null || true

# 鏋勫缓棰勮 ffmpeg 鐨勯暅鍍?
echo "Building ffmpeg image (first time may take 1-2 min)..."
docker build -t video-wallpaper:ffmpeg -f "$COMPOSE_DIR/Dockerfile" "$COMPOSE_DIR" 2>&1 | tail -3

# 鍚姩瀹瑰櫒
cd "$COMPOSE_DIR"
docker compose up -d 2>&1
sleep 5

# 娉ㄥ唽搴旂敤鍒版暟鎹簱
python3 << 'PYEOF'
import sqlite3, os, time, json

db_path = "/opt/roceos/data/roceos.db"
if os.path.exists(db_path):
    try:
        db = sqlite3.connect(db_path)
        cursor = db.cursor()

        # 璇诲彇 compose 鏂囦欢鍐呭
        with open("/opt/roceos/apps/video-wallpaper/docker-compose.yml") as f:
            compose_content = f.read()

        cursor.execute("SELECT id FROM installed_apps WHERE app_id='video-wallpaper'")
        if cursor.fetchone():
            cursor.execute("""
                UPDATE installed_apps
                SET status='running', version='1.7.2', compose_file=?,
                    install_path='/opt/roceos/apps/video-wallpaper',
                    window_type='webapp', webapp_url='/apps/video-wallpaper/',
                    updated_at=datetime('now')
                WHERE app_id='video-wallpaper'
            """, (compose_content,))
        else:
            cursor.execute("""
                INSERT INTO installed_apps
                (user_id, app_id, app_type, name, icon_url, version, status, config,
                 compose_file, install_path, window_type, webapp_port, webapp_url,
                 created_at, updated_at)
                VALUES (1, 'video-wallpaper', 'docker', 'Video Wallpaper',
                        '/api/v1/icons/vito-deploy.svg', '1.7.2', 'running',
                        '{"HTTP_PORT":8686,"VERSION":"1.7.2"}',
                        ?, '/opt/roceos/apps/video-wallpaper',
                        'webapp', 8686, '/apps/video-wallpaper/',
                        datetime('now'), datetime('now'))
            """, (compose_content,))
        db.commit()
        db.close()
        print("App registered in database")
    except Exception as e:
        print("Warning:", e)
PYEOF

# 鐧诲綍骞跺悓姝?Docker 搴旂敤
TOKEN=$(curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Angel881020"}' 2>/dev/null | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('accessToken',''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    curl -s -X POST http://127.0.0.1:8080/api/v1/appstore/sync-from-docker \
      -H "Authorization: Bearer $TOKEN" >/dev/null 2>&1
    echo "Synced with app store"
fi

# 鑷姩鍒涘缓妗岄潰蹇嵎鏂瑰紡锛堟壘绌轰綅锛?
python3 << 'PYEOF'
import sqlite3, json, time

db = sqlite3.connect("/opt/roceos/data/roceos.db")
cursor = db.cursor()
cursor.execute("SELECT icon_positions FROM desktop_layouts WHERE user_id=1")
positions = json.loads(cursor.fetchone()[0])

# 绉婚櫎鏃х殑
positions = [p for p in positions if p.get('label') != 'Video Wallpaper']

# 鎵剧┖浣?
occupied = set((p['x'], p['y']) for p in positions)
found = None
for col in range(20):
    x = 16 + col * 100
    for row in range(5):
        y = 16 + row * 110
        if (x, y) not in occupied:
            found = (x, y)
            break
    if found:
        break
if not found:
    found = (16, 676)

x, y = found
shortcut = {
    "id": f"shortcut-{int(time.time()*1000)}",
    "x": x, "y": y,
    "label": "Video Wallpaper",
    "iconType": "custom",
    "windowTitle": "Video Wallpaper",
    "customIcon": "/api/v1/icons/vito-deploy.svg",
    "shortcutUrl": "http://192.168.100.1:8686",
    "openMode": "iframe"
}
positions.append(shortcut)
cursor.execute("UPDATE desktop_layouts SET icon_positions=? WHERE user_id=1",
               (json.dumps(positions),))
db.commit()
db.close()
print(f"Desktop shortcut created at ({x}, {y})")
PYEOF

echo ""
echo "=== Installation Complete ==="
echo "Access: http://192.168.100.1:$PORT"
echo "Default video dir: /opt/video-wallpaper/videos"
echo "Desktop shortcut: auto-created"
echo "See 瑙嗛澹佺焊鎻掍欢璇存槑涔?md for full documentation"
