/**
 * API 调用模块
 */
const API_BASE = '/api';

const API = {
  async request(method, path, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);
    try {
      const res = await fetch(API_BASE + path, opts);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: '请求失败' }));
        throw new Error(err.error || '请求失败');
      }
      return await res.json();
    } catch (e) {
      if (e.message !== '请求失败') throw e;
      throw e;
    }
  },

  get: (path) => API.request('GET', path),
  post: (path, body) => API.request('POST', path, body),

  // 游戏管理
  getCharacters: () => API.get('/characters'),
  newGame: (character, name, ascension = 0) => API.post('/new_game', { character, name, ascension }),
  getState: (gameId) => API.get(`/state?game_id=${gameId}`),

  // 地图
  getMap: (gameId) => API.get(`/map?game_id=${gameId}`),
  selectNode: (gameId, nodeId) => API.post('/select_node', { game_id: gameId, node_id: nodeId }),

  // 战斗
  playCard: (gameId, cardIndex, targetIndex) =>
    API.post('/combat/play_card', { game_id: gameId, card_index: cardIndex, target_index: targetIndex }),
  endTurn: (gameId) => API.post('/combat/end_turn', { game_id: gameId }),

  // 卡牌奖励
  pickCard: (gameId, cardId) => API.post('/pick_card', { game_id: gameId, card_id: cardId }),
  skipCard: (gameId) => API.post('/pick_card', { game_id: gameId, skip: true }),

  // Boss遗物
  pickRelic: (gameId, relicId) => API.post('/pick_relic', { game_id: gameId, relic_id: relicId }),

  // 休息点
  rest: (gameId, action, cardId) => API.post('/rest', { game_id: gameId, action, card_id: cardId }),

  // 商店
  buyCard: (gameId, cardId) => API.post('/shop/buy_card', { game_id: gameId, card_id: cardId }),
  buyRelic: (gameId, relicId) => API.post('/shop/buy_relic', { game_id: gameId, relic_id: relicId }),
  removeCard: (gameId, cardId) => API.post('/shop/remove_card', { game_id: gameId, card_id: cardId }),
  shopHeal: (gameId) => API.post('/shop/heal', { game_id: gameId }),
  leaveShop: (gameId) => API.post('/shop/leave', { game_id: gameId }),

  // 事件
  eventChoose: (gameId, choiceIndex) =>
    API.post('/event/choose', { game_id: gameId, choice_index: choiceIndex }),

  // 查看牌组
  getDeck: (gameId) => API.get(`/deck?game_id=${gameId}`),

  // 排行榜
  getLeaderboard: (limit = 20) => API.get(`/leaderboard?limit=${limit}`),
  getActivePlayers: () => API.get('/active_players'),

  // 药水
  usePotion: (gameId, potionIndex, targetIndex) =>
    API.post('/use_potion', { game_id: gameId, potion_index: potionIndex, target_index: targetIndex }),
  buyPotion: (gameId, potionId) =>
    API.post('/shop/buy_potion', { game_id: gameId, potion_id: potionId }),
};
