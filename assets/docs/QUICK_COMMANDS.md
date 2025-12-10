## 后端启动（WSL2）

```
$env:PYTHONPATH="D:\Project\Wordloom\WordloomBackend\api" ; python -m uvicorn app.main_orbit:app --reload --host 127.0.0.1 --port 18080

$env:PYTHONPATH="d:\Project\Wordloom\WordloomFrontend\next\src" ;  npm run dev -- --hostname 127.0.0.1 --port 6001

### 快速启动（已安装依赖）
```bash
cd /mnt/d/Project/Wordloom/frontend
npm run dev

cd /mnt/d/Project/Wordloom/backend
source .venv_linux/bin/activate
uvicorn api.app.main:app --host 0.0.0.0 --port 30001 --reload
```

## 前端启动（Windows PowerShell）
```powershell
cd d:\Project\Wordloom\frontend
npm install
npm run dev
```

## 目录导航
```bash
cd /mnt/d/Project/Wordloom/frontend
cd /mnt/d/Project/Wordloom/backend
```

wsl

sudo service postgresql status
# 或者有些系统是：
sudo systemctl status postgresql

sudo service postgresql start
# 或
sudo systemctl start postgresql

