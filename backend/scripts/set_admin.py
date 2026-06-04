"""One-time script: set a user as admin

Usage:
  python scripts/set_admin.py <username>

Example:
  python scripts/set_admin.py xiaodaishu
"""

import sys
import sqlite3
from pathlib import Path

# 找数据库文件
db_paths = [
    Path(__file__).parent.parent / "woostudy.db",
    Path.cwd() / "woostudy.db",
    Path.cwd() / "app" / "woostudy.db",
]
db_path = None
for p in db_paths:
    if p.exists():
        db_path = p
        break

if not db_path:
    print("[ERROR] 未找到 woostudy.db，请确保在项目目录下运行")
    sys.exit(1)

if len(sys.argv) < 2:
    print("用法: python scripts/set_admin.py <用户名>")
    sys.exit(1)

username = sys.argv[1]

conn = sqlite3.connect(str(db_path))
cursor = conn.execute("SELECT id, username, role FROM users WHERE username = ?", (username,))
row = cursor.fetchone()

if not row:
    print(f"[ERROR] 用户 [{username}] 不存在，请先注册")
    cursor2 = conn.execute("SELECT id, username FROM users")
    users = cursor2.fetchall()
    if users:
        print("现有用户:")
        for u in users:
            print(f"  ID={u[0]}  {u[1]}")
    conn.close()
    sys.exit(1)

user_id, uname, current_role = row

# 加 role 列（如果还没加）
try:
    conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
except Exception:
    pass

conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user_id,))
conn.commit()
conn.close()
print(f"[OK] 已将 [{uname}] (ID={user_id}) 设为管理员")
