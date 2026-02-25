/**
 * 游戏主逻辑 - 状态机与事件处理
 */
const Game = {
  // 游戏状态
  gameId: null,
  state: null,
  selectedCharacter: null,
  selectedEnemy: 0,
  isProcessing: false,

  // ===== 初始化 =====
  async init() {
    await this.loadCharacters();
    UI.showScreen('menu');
  },

  async loadCharacters() {
    try {
      const data = await API.getCharacters();
      this.renderCharacterList(data.characters);
    } catch (e) {
      console.error('加载职业失败', e);
    }
  },

  renderCharacterList(characters) {
    const list = document.getElementById('character-list');
    list.innerHTML = '';
    characters.forEach(char => {
      const atkStr = char.char_attack_bonus > 0 ? `+${char.char_attack_bonus}` : `${char.char_attack_bonus}`;
      const defStr = char.char_defense_bonus > 0 ? `+${char.char_defense_bonus}` : `${char.char_defense_bonus}`;
      const atkColor = char.char_attack_bonus >= 0 ? '#e74c3c' : '#888';
      const defColor = char.char_defense_bonus >= 0 ? '#3498db' : '#888';
      const card = document.createElement('div');
      card.className = 'character-card';
      card.innerHTML = `
        <div class="char-icon">${char.icon}</div>
        <div class="char-name">${char.name}</div>
        <div class="char-stats-mini">
          <span>❤️ ${char.max_hp}</span>
          <span>⚡ ${char.max_energy}</span>
          <span style="color:${atkColor}">⚔️ ${atkStr}</span>
          <span style="color:${defColor}">🛡️ ${defStr}</span>
        </div>
      `;
      card.addEventListener('click', () => this.selectCharacter(char, card));
      list.appendChild(card);
    });
  },

  // ===== 菜单导航 =====
  showMenu() {
    this.gameId = null;
    this.state = null;
    this.selectedCharacter = null;
    UI.showScreen('menu');
  },

  showCharacterSelect() {
    UI.showScreen('character');
    document.getElementById('character-confirm').classList.add('hidden');
  },

  async showLeaderboard() {
    UI.showScreen('leaderboard');
    const el = document.getElementById('leaderboard-content');
    if (el) el.innerHTML = '<div class="loading">加载中...</div>';
    try {
      const data = await API.getLeaderboard(20);
      UI.renderLeaderboard(data.entries, data.stats);
    } catch (e) {
      if (el) el.innerHTML = '<div class="loading">暂无数据</div>';
    }
  },

  selectCharacter(char, cardEl) {
    this.selectedCharacter = char;
    document.querySelectorAll('.character-card').forEach(c => c.classList.remove('selected'));
    cardEl.classList.add('selected');

    const atkBonus = char.char_attack_bonus;
    const defBonus = char.char_defense_bonus;
    const atkStr = atkBonus > 0 ? `<span style="color:#e74c3c">+${atkBonus}</span>` : atkBonus < 0 ? `<span style="color:#888">${atkBonus}</span>` : `<span style="color:#aaa">0</span>`;
    const defStr = defBonus > 0 ? `<span style="color:#3498db">+${defBonus}</span>` : defBonus < 0 ? `<span style="color:#888">${defBonus}</span>` : `<span style="color:#aaa">0</span>`;
    const passiveRow = char.base_block > 0
      ? `<div class="char-detail-row"><span>🛡️ 被动护甲</span><span style="color:#3498db">每回合 +${char.base_block}</span></div>`
      : '';
    document.getElementById('character-detail').innerHTML = `
      <div class="char-detail-panel">
        <div style="font-size:44px;text-align:center">${char.icon}</div>
        <div style="font-size:18px;font-weight:bold;text-align:center;margin:6px 0">${char.name}</div>
        <div style="color:var(--text-secondary);font-size:12px;text-align:center;margin-bottom:12px">${char.description}</div>
        <div class="char-detail-row"><span>❤️ 生命值</span><span style="color:#27ae60">${char.max_hp}</span></div>
        <div class="char-detail-row"><span>⚡ 能量上限</span><span style="color:#f39c12">${char.max_energy}</span></div>
        <div class="char-detail-row"><span>⚔️ 攻击加成/hit</span>${atkStr}</div>
        <div class="char-detail-row"><span>🛡️ 格挡加成/次</span>${defStr}</div>
        ${passiveRow}
      </div>
    `;

    document.getElementById('character-confirm').classList.remove('hidden');
    document.getElementById('btn-start-game').onclick = () => this.startGame();
  },

  // ===== 开始游戏 =====
  async startGame() {
    if (!this.selectedCharacter) {
      UI.notify('请先选择职业！', 'warning');
      return;
    }
    if (this.isProcessing) return;
    this.isProcessing = true;

    const name = document.getElementById('player-name').value.trim() || '无名英雄';
    const ascensionEl = document.getElementById('ascension-select');
    const ascension = ascensionEl ? parseInt(ascensionEl.value || '0') : 0;

    try {
      const data = await API.newGame(this.selectedCharacter.id, name, ascension);
      this.gameId = data.game_id;
      UI.notify(`游戏开始！欢迎，${name}！`, 'success', 2000);
      await this.refreshState();
    } catch (e) {
      UI.notify('开始游戏失败：' + e.message, 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  // ===== 状态刷新 =====
  async refreshState() {
    if (!this.gameId) return;
    try {
      const state = await API.getState(this.gameId);
      this.applyState(state);
    } catch (e) {
      UI.notify('状态刷新失败', 'error');
    }
  },

  applyState(state) {
    if (!state) return;
    this.state = state;
    const player = state.player;
    const phase = state.phase;

    // 更新顶部状态栏（战斗和地图屏幕）
    if (['map', 'shop', 'rest', 'event', 'card_reward', 'boss_relic'].includes(phase)) {
      UI.updateHeader(player);
    }

    // 显示消息
    if (state.message) {
      const msgEl = document.getElementById('map-message');
      if (msgEl) msgEl.textContent = state.message;
    }

    switch (phase) {
      case 'map':
        UI.showScreen('map');
        UI.updateHeader(player);
        UI.renderMap(state.map, (nodeId) => this.selectNode(nodeId));
        document.getElementById('map-message').textContent = state.message || '';
        break;

      case 'combat':
        UI.showScreen('combat');
        this.renderCombatState(state);
        break;

      case 'card_reward':
        UI.showScreen('card-reward');
        document.getElementById('reward-message').textContent = state.message || '';
        UI.renderCardRewards(state.card_rewards || [], (cardId) => this.pickCard(cardId));
        break;

      case 'boss_relic':
        UI.showScreen('boss-relic');
        UI.renderBossRelics(state.boss_relic_choices || [], (relicId) => this.pickRelic(relicId));
        break;

      case 'shop':
        UI.showScreen('shop');
        UI.renderShop(
          state.shop,
          player,
          (cardId) => this.buyCard(cardId),
          (relicId) => this.buyRelic(relicId),
          (potionId) => this.buyPotion(potionId),
          (price) => this.showRemoveCardUI(price),
          () => this.shopHeal()
        );
        break;

      case 'rest':
        UI.showScreen('rest');
        document.getElementById('upgrade-select').classList.add('hidden');
        break;

      case 'event':
        UI.showScreen('event');
        UI.renderEvent(state.event, (idx) => this.eventChoose(idx));
        break;

      case 'game_over':
        UI.showScreen('game-over');
        UI.renderStats(player, 'game-over-stats', state.final_stats, state.ascension_name);
        break;

      case 'victory':
        UI.showScreen('victory');
        UI.renderStats(player, 'victory-stats', state.final_stats, state.ascension_name);
        break;
    }
  },

  // ===== 地图操作 =====
  async selectNode(nodeId) {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.selectNode(this.gameId, nodeId);
      if (state.combat) {
        UI.clearLog();
      }
      this.applyState(state);
    } catch (e) {
      UI.notify('操作失败：' + e.message, 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  // ===== 战斗操作 =====
  renderCombatState(state) {
    UI.renderCombat(state, this.selectedEnemy,
      (cardIdx) => this.playCard(cardIdx),
      (enemyIdx) => this.selectEnemy(enemyIdx)
    );
    // 确保目标合法
    const enemies = (state.combat?.enemies || []).filter(e => e.hp > 0);
    if (this.selectedEnemy >= enemies.length) this.selectedEnemy = 0;
  },

  selectEnemy(idx) {
    this.selectedEnemy = idx;
    // 重新渲染突出显示
    document.querySelectorAll('.enemy-card').forEach((el, i) => {
      el.classList.toggle('targeted', i === idx);
    });
  },

  async playCard(cardIndex) {
    if (this.isProcessing) return;
    this.isProcessing = true;

    const targetIndex = this.selectedEnemy;

    try {
      const state = await API.playCard(this.gameId, cardIndex, targetIndex);
      // Flash enemy on damage
      if (state.log && state.log.some(l => l.includes('伤害') && !l.includes('你受到'))) {
        UI.flashElement(`enemy-card-${targetIndex}`, 'damage');
      }
      this.applyState(state);
      if (state.log) UI.appendLog(state.log);

      if (state.combat_result === 'victory') {
        UI.notify('⚔️ 战斗胜利！', 'success', 2000);
      } else if (state.combat_result === 'defeat') {
        UI.notify('💀 你已倒下...', 'error', 3000);
      }
    } catch (e) {
      UI.notify(e.message || '打牌失败', 'warning');
    } finally {
      this.isProcessing = false;
    }
  },

  async endTurn() {
    if (this.isProcessing) return;
    if (!this.gameId) return;
    this.isProcessing = true;

    try {
      const state = await API.endTurn(this.gameId);
      // Flash player HP bar when taking damage from enemies
      if (state.log && state.log.some(l => l.includes('你受到'))) {
        UI.flashElement('header-hp', 'damage');
      }
      this.applyState(state);
      if (state.log) UI.appendLog(state.log);

      if (state.combat_result === 'defeat') {
        UI.notify('💀 你已倒下...', 'error', 3000);
      }
    } catch (e) {
      UI.notify('操作失败：' + e.message, 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  // ===== 卡牌奖励 =====
  async pickCard(cardId) {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.pickCard(this.gameId, cardId);
      UI.notify('已将卡牌加入牌组！', 'success', 1500);
      this.applyState(state);
    } catch (e) {
      UI.notify('操作失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  async skipCardReward() {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.skipCard(this.gameId);
      this.applyState(state);
    } catch (e) {
      UI.notify('操作失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  // ===== Boss遗物 =====
  async pickRelic(relicId) {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.pickRelic(this.gameId, relicId);
      UI.notify('✨ 已获得遗物！', 'success', 2000);
      this.applyState(state);
    } catch (e) {
      UI.notify('操作失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  // ===== 休息点 =====
  async restHeal() {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.rest(this.gameId, 'heal');
      UI.notify(state.message || '休息恢复了HP！', 'success', 2000);
      this.applyState(state);
    } catch (e) {
      UI.notify('操作失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  showUpgradeSelect() {
    const upgradeDiv = document.getElementById('upgrade-select');
    upgradeDiv.classList.remove('hidden');
    const deck = this.state?.player?.deck || [];
    UI.renderUpgradeDeck(deck, (cardId) => this.upgradeCard(cardId));
  },

  async upgradeCard(cardId) {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.rest(this.gameId, 'upgrade', cardId);
      UI.notify(state.message || '卡牌已升级！', 'success', 2000);
      this.applyState(state);
    } catch (e) {
      UI.notify('升级失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  // ===== 商店操作 =====
  async buyCard(cardId) {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.buyCard(this.gameId, cardId);
      UI.notify(state.message || '购买成功！', 'success', 2000);
      this.applyState(state);
    } catch (e) {
      UI.notify(e.message || '购买失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  async buyRelic(relicId) {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.buyRelic(this.gameId, relicId);
      UI.notify(state.message || '遗物购买成功！', 'success', 2000);
      this.applyState(state);
    } catch (e) {
      UI.notify(e.message || '购买失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  showRemoveCardUI(price) {
    // 简单实现：弹出选择界面
    const deck = this.state?.player?.deck || [];
    if (deck.length === 0) {
      UI.notify('牌组为空', 'warning');
      return;
    }

    // 创建临时弹窗
    const modal = document.createElement('div');
    modal.style.cssText = `
      position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:2000;
      display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;
    `;
    modal.innerHTML = `
      <h3 style="color:var(--text-primary)">选择要移除的卡牌（费用: ${price} 金币）</h3>
      <div id="remove-card-grid" style="display:flex;flex-wrap:wrap;gap:10px;max-width:800px;justify-content:center;overflow-y:auto;max-height:60vh;padding:16px;"></div>
      <button class="btn btn-secondary" onclick="this.parentElement.remove()">取消</button>
    `;
    document.body.appendChild(modal);

    const grid = modal.querySelector('#remove-card-grid');
    deck.forEach(card => {
      const el = UI.createCardElement(card, false);
      el.style.cursor = 'pointer';
      el.addEventListener('click', async () => {
        modal.remove();
        await this.removeCard(card.id);
      });
      grid.appendChild(el);
    });
  },

  async removeCard(cardId) {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.removeCard(this.gameId, cardId);
      UI.notify(state.message || '卡牌已移除！', 'success', 2000);
      this.applyState(state);
    } catch (e) {
      UI.notify(e.message || '移除失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  async buyPotion(potionId) {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.buyPotion(this.gameId, potionId);
      UI.notify(state.message || '药水购买成功！', 'success', 2000);
      this.applyState(state);
    } catch (e) {
      UI.notify(e.message || '购买失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  async shopHeal() {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.shopHeal(this.gameId);
      UI.notify(state.message || '治疗成功！', 'success', 2000);
      this.applyState(state);
    } catch (e) {
      UI.notify(e.message || '治疗失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  async leaveShop() {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.leaveShop(this.gameId);
      this.applyState(state);
    } catch (e) {
      UI.notify('操作失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  // ===== 事件处理 =====
  async eventChoose(choiceIndex) {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const data = await API.eventChoose(this.gameId, choiceIndex);
      UI.notify(data.message || '事件已处理', 'info', 2500);
      this.applyState(data);
    } catch (e) {
      UI.notify('操作失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  // ===== 药水操作 =====
  async usePotion(potionIndex) {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const state = await API.usePotion(this.gameId, potionIndex, this.selectedEnemy);
      if (state.log) UI.appendLog(state.log);
      this.applyState(state);
    } catch (e) {
      UI.notify(e.message || '使用药水失败', 'error');
    } finally {
      this.isProcessing = false;
    }
  },

  // ===== 查看牌组 =====
  async viewDeck() {
    if (!this.gameId) return;
    try {
      const data = await API.getDeck(this.gameId);
      const modal = document.getElementById('modal-deck');
      const cards = document.getElementById('modal-deck-cards');
      cards.innerHTML = '';
      (data.deck || []).forEach(card => {
        const el = UI.createCardElement(card, false);
        el.style.cursor = 'default';
        cards.appendChild(el);
      });
      modal.classList.remove('hidden');
    } catch (e) {
      UI.notify('查看失败', 'error');
    }
  },

  closeDeckModal() {
    document.getElementById('modal-deck').classList.add('hidden');
  },
};

// ===== 键盘快捷键 =====
document.addEventListener('keydown', (e) => {
  if (Game.state?.phase !== 'combat') return;
  const hand = Game.state.hand || [];

  // 数字键1-9打出对应手牌
  const num = parseInt(e.key);
  if (num >= 1 && num <= 9 && num <= hand.length) {
    Game.playCard(num - 1);
  }

  // E键结束回合
  if (e.key === 'e' || e.key === 'E') {
    Game.endTurn();
  }

  // Tab切换目标
  if (e.key === 'Tab') {
    e.preventDefault();
    const allEnemies = Game.state.combat?.enemies || [];
    const aliveIndices = allEnemies.map((en, i) => en.hp > 0 ? i : -1).filter(i => i >= 0);
    if (aliveIndices.length > 1) {
      const currentPos = aliveIndices.indexOf(Game.selectedEnemy);
      const nextPos = (currentPos + 1) % aliveIndices.length;
      Game.selectedEnemy = aliveIndices[nextPos];
      document.querySelectorAll('.enemy-card').forEach((el, i) => {
        el.classList.toggle('targeted', i === Game.selectedEnemy);
      });
    }
  }
});

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
  Game.init().catch(console.error);
});
