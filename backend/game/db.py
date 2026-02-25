"""数据库模块 - SQLite 持久化存储，支持多人游玩"""
import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = os.environ.get('DB_PATH', '/app/data/textgame.db')


def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    with _get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS games (
                game_id     TEXT PRIMARY KEY,
                player_name TEXT DEFAULT '',
                character   TEXT DEFAULT '',
                phase       TEXT DEFAULT 'map',
                floor       INTEGER DEFAULT 0,
                state_json  TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name     TEXT NOT NULL,
                character       TEXT NOT NULL,
                character_icon  TEXT DEFAULT '',
                ascension       INTEGER DEFAULT 0,
                floor           INTEGER DEFAULT 0,
                kills           INTEGER DEFAULT 0,
                turns           INTEGER DEFAULT 0,
                cards_played    INTEGER DEFAULT 0,
                damage_dealt    INTEGER DEFAULT 0,
                damage_taken    INTEGER DEFAULT 0,
                result          TEXT NOT NULL,
                score           INTEGER DEFAULT 0,
                created_at      TEXT NOT NULL
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_leaderboard_score ON leaderboard(score DESC)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_games_updated ON games(updated_at)')
        conn.commit()


def save_game(game_id: str, state: dict):
    """保存游戏状态到数据库"""
    now = datetime.utcnow().isoformat()
    player = state.get('player', {})
    with _get_conn() as conn:
        conn.execute('''
            INSERT INTO games (game_id, player_name, character, phase, floor, state_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                player_name = excluded.player_name,
                character   = excluded.character,
                phase       = excluded.phase,
                floor       = excluded.floor,
                state_json  = excluded.state_json,
                updated_at  = excluded.updated_at
        ''', (
            game_id,
            player.get('name', ''),
            player.get('character', ''),
            state.get('phase', 'map'),
            player.get('floor', 0),
            json.dumps(state, ensure_ascii=False),
            now, now
        ))
        conn.commit()


def get_game(game_id: str) -> dict:
    """从数据库读取游戏状态"""
    with _get_conn() as conn:
        row = conn.execute(
            'SELECT state_json FROM games WHERE game_id = ?', (game_id,)
        ).fetchone()
        if row:
            return json.loads(row['state_json'])
    return None


def get_active_games(limit: int = 20) -> list:
    """获取当前活跃的游戏列表（用于显示在线人数）"""
    cutoff = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    with _get_conn() as conn:
        rows = conn.execute('''
            SELECT game_id, player_name, character, phase, floor, updated_at
            FROM games
            WHERE updated_at > ? AND phase NOT IN ('game_over', 'victory')
            ORDER BY updated_at DESC
            LIMIT ?
        ''', (cutoff, limit)).fetchall()
        return [dict(r) for r in rows]


def cleanup_old_games(hours: int = 2):
    """清理超过指定小时的旧游戏（释放内存/磁盘）"""
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    with _get_conn() as conn:
        result = conn.execute('DELETE FROM games WHERE updated_at < ?', (cutoff,))
        conn.commit()
        return result.rowcount


def record_run(player: dict, result: str, ascension: int):
    """将一局游戏记录到排行榜"""
    floor = player.get('floor', 0)
    kills = player.get('kills', 0)
    turns = player.get('turns', 0)
    cards = player.get('cards_played', 0)
    dmg_dealt = player.get('damage_dealt', 0)
    dmg_taken = player.get('damage_taken', 0)

    # 评分公式：楼层×100 + 击杀×10 + 天赋×500，胜利翻倍
    score = floor * 100 + kills * 10 + ascension * 500
    if result == 'victory':
        score = score * 2 + 1000

    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        conn.execute('''
            INSERT INTO leaderboard
                (player_name, character, character_icon, ascension, floor, kills, turns,
                 cards_played, damage_dealt, damage_taken, result, score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            player.get('name', '无名英雄'),
            player.get('character_name', ''),
            player.get('character_icon', ''),
            ascension, floor, kills, turns, cards,
            dmg_dealt, dmg_taken, result, score, now
        ))
        conn.commit()


def get_leaderboard(limit: int = 20) -> list:
    """获取排行榜（按分数降序）"""
    with _get_conn() as conn:
        rows = conn.execute('''
            SELECT player_name, character, character_icon, ascension, floor, kills,
                   turns, cards_played, damage_dealt, damage_taken, result, score, created_at
            FROM leaderboard
            ORDER BY score DESC, floor DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_stats_summary() -> dict:
    """全局统计概览"""
    with _get_conn() as conn:
        total = conn.execute('SELECT COUNT(*) as n FROM leaderboard').fetchone()['n']
        victories = conn.execute(
            "SELECT COUNT(*) as n FROM leaderboard WHERE result='victory'"
        ).fetchone()['n']
        best = conn.execute(
            'SELECT MAX(floor) as f FROM leaderboard'
        ).fetchone()['f'] or 0
        active = conn.execute('''
            SELECT COUNT(*) as n FROM games
            WHERE updated_at > ? AND phase NOT IN ('game_over','victory')
        ''', ((datetime.utcnow() - timedelta(hours=1)).isoformat(),)).fetchone()['n']

    return {
        'total_runs': total,
        'victories': victories,
        'best_floor': best,
        'active_players': active,
        'win_rate': round(victories / total * 100, 1) if total > 0 else 0,
    }


# 启动时初始化
init_db()
