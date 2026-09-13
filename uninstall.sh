#!/bin/bash
echo "=== Video Wallpaper Uninstaller ==="

# 停止并删除容器
docker stop video-wallpaper 2>/dev/null || true
docker rm video-wallpaper 2>/dev/null || true
echo "Container removed"

# 恢复登录页面
WWW_DIR="/opt/roceos/www"
if [ -f "$WWW_DIR/index.html.bak" ]; then
    cp "$WWW_DIR/index.html.bak" "$WWW_DIR/index.html"
    echo "Restored index.html"
fi

# 删除符号链接
rm -f "$WWW_DIR/assets/wallpapers"

# 删除桌面快捷方式（多种匹配方式）
python3 << 'PYEOF'
import sqlite3, json, os

db_path = "/opt/roceos/data/roceos.db"
if os.path.exists(db_path):
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    cursor.execute("SELECT icon_positions FROM desktop_layouts WHERE user_id=1")
    row = cursor.fetchone()
    if row and row[0]:
        positions = json.loads(row[0])
        before = len(positions)
        positions = [p for p in positions if not (
            p.get('label') == 'Video Wallpaper' or
            p.get('windowTitle') == 'Video Wallpaper' or
            p.get('shortcutUrl') == 'http://192.168.100.1:8686' or
            (p.get('id','').startswith('shortcut-') and 'video-wallpaper' in p.get('shortcutUrl','').lower())
        )]
        cursor.execute("UPDATE desktop_layouts SET icon_positions=? WHERE user_id=1",
                       (json.dumps(positions),))
        db.commit()
        print(f"Removed {before - len(positions)} desktop shortcut(s)")
    db.close()
PYEOF

# 删除应用注册
python3 << 'PYEOF'
import sqlite3, os
db_path = "/opt/roceos/data/roceos.db"
if os.path.exists(db_path):
    db = sqlite3.connect(db_path)
    db.execute("DELETE FROM installed_apps WHERE app_id='video-wallpaper'")
    db.commit()
    db.close()
    print("Removed app registration")
PYEOF

# 删除文件
rm -rf /opt/video-wallpaper
rm -rf /opt/roceos/apps/video-wallpaper
echo "Removed files"

echo ""
echo "=== Uninstall Complete ==="
