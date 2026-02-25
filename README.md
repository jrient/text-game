# 深渊征途 · Abyss Journey

类 Slay the Spire 风格的文字肉鸽卡牌游戏，运行在浏览器中，支持多人同时在线。

## 特性

- **3 种职业**：战士 / 法师 / 刺客，各有独特牌组
- **65+ 张卡牌**，55+ 种遗物，10 种药水，10 种随机事件
- **6 级天赋难度**（0-5），挑战越高评分越高
- **永久死亡**肉鸽机制，3 幕结构随机地图
- **多人支持**：SQLite 持久化，服务器重启不丢档

## 快速开始

```bash
docker compose up -d
```

访问 [http://textgame.al.jrient.cn](http://textgame.al.jrient.cn)

## 本地开发

```bash
cd backend
pip install -r requirements.txt
export DB_PATH=/tmp/textgame.db
python app.py
# http://localhost:5000
```

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11 · Flask · SQLite |
| 前端 | 原生 HTML / CSS / JS |
| 部署 | Docker · docker compose |

## 项目结构

```
text-game/
├── backend/
│   ├── app.py          # 主应用，22 个 REST API
│   └── game/           # 游戏核心逻辑
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/             # api.js · ui.js · game.js
├── Dockerfile
└── docker-compose.yml
```

## 评分公式

```
基础分 = 层数 × 100 + 击杀数 × 10 + 天赋等级 × 500
胜利分 = 基础分 × 2 + 1000
```

## 快捷键

| 键 | 操作 |
|----|------|
| `1` - `9` | 打出卡牌 |
| `E` | 结束回合 |
| `Tab` | 切换目标 |
