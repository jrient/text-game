# 深渊征途 · Abyss Journey

> 类 Slay the Spire 风格的文字肉鸽卡牌游戏，运行在浏览器中，支持多人同时在线。

## 特性

- **3 种职业**：战士 / 法师 / 刺客，各有独特牌组与起始遗物
- **80+ 张卡牌**，55+ 种遗物，10 种药水，10 种随机事件
- **3 幕随机地图**：战斗、精英、篝火、商店、事件、宝箱、Boss
- **法球系统**（法师专属）：闪电 / 冰霜 / 等离子体，被动 + 激活双重效果
- **永久死亡**肉鸽机制，每局随机性保证重玩价值
- **多人支持**：SQLite 持久化，服务器重启不丢档，多人同时在线独立存档
- **移动端适配**：长按卡牌查看详情，触控友好布局

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

| 层   | 技术                          |
|------|-------------------------------|
| 后端 | Python 3.11 · Flask · SQLite  |
| 前端 | 原生 HTML / CSS / JS          |
| 部署 | Docker · docker compose       |

## 项目结构

```
text-game/
├── backend/
│   ├── app.py               # 主应用，REST API 路由
│   └── game/
│       ├── state.py         # 游戏状态管理
│       ├── combat.py        # 战斗核心逻辑 & 卡牌效果
│       ├── cards.py         # 卡牌定义（战士/法师/刺客）
│       ├── enemies.py       # 敌人 & Boss 定义
│       ├── relics.py        # 遗物定义
│       ├── relic_effects.py # 遗物触发逻辑
│       ├── map_gen.py       # 节点地图生成
│       ├── events.py        # 随机事件
│       └── potions.py       # 药水系统
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js           # API 通信层
│       ├── ui.js            # UI 渲染
│       └── game.js          # 游戏流程控制
├── Dockerfile
└── docker-compose.yml
```

## 评分公式

```
基础分 = 层数 × 100 + 击杀数 × 10
胜利分 = 基础分 × 2 + 1000
```

## 快捷键

| 键       | 操作         |
|----------|--------------|
| `1`–`9`  | 打出卡牌     |
| `E`      | 结束回合     |
| `Tab`    | 切换目标敌人 |

## 游戏手册

详细游戏规则、职业介绍、卡牌/遗物说明见 [MANUAL.md](MANUAL.md)。
