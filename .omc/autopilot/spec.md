# 文字肉鸽游戏 - 技术规格文档

## 游戏概念
类Slay the Spire风格的文字肉鸽卡牌游戏，全Web界面，支持完整的Roguelike体验。

## 核心特性
### 职业系统（3个）
- **战士**：高血量，擅长力量和防御，卡牌偏向重攻击
- **法师**：低血量，擅长魔法连击和能量管理
- **刺客**：中等血量，擅长毒素和连续攻击

### 地图系统
- 节点地图（类似Slay the Spire分支路径）
- 节点类型：普通战斗、精英战斗、休息点、商店、随机事件、Boss
- 3幕结构，每幕15-20个节点

### 卡牌系统
- 每职业20+张独特卡牌
- 类型：攻击、防御、技能、能力（永久效果）
- 回合开始：抽5张，获得3点能量
- 战斗奖励：选1/3张新卡

### 遗物系统
- 30+种遗物，提供被动效果
- 来源：Boss奖励、商店购买、事件

### 战斗系统
- 回合制：玩家出牌 → 敌人行动
- 状态效果：力量、敏捷、虚弱、脆弱、毒素、灼烧
- 敌人有意图显示（攻击/防御/特殊）

### Boss战
- 第1幕Boss：守卫者（盾牌机制）
- 第2幕Boss：六边形幽灵（相位穿越）
- 第3幕Boss：腐败之心（最终Boss）

## 技术架构
### 后端：Python Flask
- RESTful API
- 游戏状态存储在服务器Session
- 纯Python游戏逻辑

### 前端：原生HTML/CSS/JS
- 响应式设计，暗色主题
- 动画效果（CSS transitions）
- 无框架依赖，纯Vanilla JS

### Docker部署
- Python 3.11 Alpine镜像
- Nginx反向代理
- docker-compose一键启动

## 文件结构
```
text-game/
├── backend/
│   ├── app.py              # Flask主文件+路由
│   ├── game/
│   │   ├── __init__.py
│   │   ├── state.py        # 游戏状态管理
│   │   ├── cards.py        # 卡牌定义
│   │   ├── relics.py       # 遗物定义
│   │   ├── enemies.py      # 敌人定义
│   │   ├── map_gen.py      # 地图生成
│   │   ├── combat.py       # 战斗逻辑
│   │   └── events.py       # 随机事件
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js          # API调用
│       ├── ui.js           # UI渲染
│       └── game.js         # 主游戏逻辑
├── nginx/nginx.conf
├── Dockerfile
├── docker-compose.yml
└── README.md
```
