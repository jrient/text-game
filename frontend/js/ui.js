/**
 * UI 渲染模块
 */
const UI = {
  // ===== 屏幕切换 =====
  showScreen(name) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById(`screen-${name}`);
    if (screen) screen.classList.add('active');
  },

  // ===== 通知 =====
  notify(msg, type = 'info', duration = 3000) {
    const el = document.getElementById('notification');
    el.textContent = msg;
    el.className = `notification notification-${type}`;
    el.classList.remove('hidden');
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.add('hidden'), duration);
  },

  // ===== 顶部状态栏 =====
  updateHeader(player) {
    if (!player) return;
    const maxHp = player.max_hp;
    const hp = player.hp;
    const pct = Math.max(0, (hp / maxHp) * 100);

    document.getElementById('header-char-icon').textContent = player.character_icon || '⚔️';
    document.getElementById('header-char-name').textContent = player.character_name || '';
    document.getElementById('header-hp').textContent = `${hp}/${maxHp}`;
    document.getElementById('header-gold').textContent = player.gold || 0;
    document.getElementById('header-floor').textContent = player.floor || 0;

    const fill = document.getElementById('header-hp-fill');
    fill.style.width = pct + '%';
    fill.className = 'hp-fill' + (pct <= 30 ? ' low' : pct <= 60 ? ' mid' : '');

    // 遗物
    const relicsEl = document.getElementById('header-relics');
    relicsEl.innerHTML = (player.relics || []).map(r => {
      const short = r.name.length > 4 ? r.name.slice(0, 4) + '…' : r.name;
      return `<div class="relic-icon" title="${r.name}: ${r.description}">${short}</div>`;
    }).join('');
  },

  // ===== 地图渲染 =====
  renderMap(mapData, onSelectNode) {
    if (!mapData) return;
    const container = document.getElementById('map-nodes');
    container.innerHTML = '';

    const nodes = mapData.nodes;
    const available = new Set(mapData.available_nodes || []);

    // 按楼层分组
    const floors = {};
    Object.values(nodes).forEach(node => {
      if (!floors[node.floor]) floors[node.floor] = [];
      floors[node.floor].push(node);
    });

    // 从低层到高层渲染（显示时反转：最高层在上）
    const sortedFloors = Object.keys(floors).sort((a, b) => a - b);

    sortedFloors.forEach(floorNum => {
      const floorDiv = document.createElement('div');
      floorDiv.className = 'map-floor';
      floorDiv.dataset.floor = floorNum;

      floors[floorNum].forEach(node => {
        const nodeEl = document.createElement('div');
        nodeEl.className = `map-node`;
        nodeEl.dataset.type = node.type;
        nodeEl.dataset.id = node.id;

        const isAvailable = available.has(node.id);
        const isVisited = node.visited;

        if (isAvailable) nodeEl.classList.add('available');
        else if (isVisited) nodeEl.classList.add('visited');
        else nodeEl.classList.add('unavailable');

        nodeEl.innerHTML = `
          <span class="node-label">${node.label}</span>
          <span class="node-floor">F${parseInt(floorNum) + 1}</span>
        `;

        if (isAvailable) {
          nodeEl.addEventListener('click', () => onSelectNode(node.id));
        }

        floorDiv.appendChild(nodeEl);
      });

      container.appendChild(floorDiv);
    });
  },

  // ===== 战斗渲染 =====
  renderCombat(state, selectedEnemy, onCardPlay, onEnemySelect) {
    if (!state) return;

    const player = state.player;
    const combat = state.combat;
    const enemies = combat ? combat.enemies : [];

    // 更新玩家状态
    this._updatePlayerCombatStatus(player);

    // 能量
    document.getElementById('combat-energy').textContent = state.energy ?? player.energy ?? 0;
    document.getElementById('combat-max-energy').textContent = player.max_energy || 3;

    // 牌堆计数
    document.getElementById('draw-count').textContent = state.draw_pile_count ?? 0;
    document.getElementById('discard-count').textContent = state.discard_pile_count ?? 0;

    // 回合
    if (combat) {
      document.getElementById('turn-indicator').textContent = `第 ${combat.turn} 回合`;
    }

    // 渲染敌人
    const enemiesArea = document.getElementById('enemies-area');
    enemiesArea.innerHTML = '';
    const aliveEnemies = enemies.filter(e => e.hp > 0);

    enemies.forEach((enemy, idx) => {
      const el = document.createElement('div');
      el.className = `enemy-card${enemy.is_boss ? ' boss' : ''}${enemy.hp <= 0 ? ' dead' : ''}`;
      if (idx === selectedEnemy && enemy.hp > 0) el.classList.add('targeted');

      const hpPct = Math.max(0, (enemy.hp / enemy.max_hp) * 100);
      const intentHtml = enemy.intent ? `
        <div class="enemy-intent">
          <div class="intent-label">${_intentIcon(enemy.intent.action)} 意图</div>
          <div>${enemy.intent.description || '??'}</div>
        </div>
      ` : '';

      const effectsHtml = [
        enemy.poison > 0 ? `<span class="enemy-poison">☠️ 毒${enemy.poison}</span>` : '',
        enemy.strength > 0 ? `<span class="status-badge strength">💪 力${enemy.strength}</span>` : '',
        enemy.weak_turns > 0 ? `<span class="status-badge weak">💔 弱${enemy.weak_turns}</span>` : '',
        enemy.vulnerable_turns > 0 ? `<span class="status-badge vulnerable">⬇️ 伤${enemy.vulnerable_turns}</span>` : '',
      ].filter(Boolean).join('');

      const typeLabel = enemy.is_boss ? '【Boss】' : enemy.is_elite ? '【精英】' : '普通';
      el.innerHTML = `
        <div class="enemy-type">${typeLabel}</div>
        <div class="enemy-name">${enemy.name}</div>
        <div class="enemy-hp-bar">
          <div class="enemy-hp-text">❤️ ${enemy.hp}/${enemy.max_hp}</div>
          <div class="hp-bar">
            <div class="hp-fill${hpPct <= 30 ? ' low' : hpPct <= 60 ? ' mid' : ''}" style="width:${hpPct}%"></div>
          </div>
        </div>
        ${enemy.block > 0 ? `<div class="enemy-block">🛡️ 格挡: ${enemy.block}</div>` : ''}
        ${effectsHtml ? `<div class="enemy-effects">${effectsHtml}</div>` : ''}
        ${intentHtml}
      `;

      if (enemy.hp > 0) {
        el.addEventListener('click', () => onEnemySelect(idx));
      }
      enemiesArea.appendChild(el);
    });

    // 渲染手牌
    const hand = state.hand || [];
    const energy = state.energy ?? 0;
    this.renderHand(hand, energy, onCardPlay);

    // 渲染药水
    this.renderPotions(state.potions || [], (idx) => Game.usePotion(idx));
  },

  _updatePlayerCombatStatus(player) {
    if (!player) return;
    const hp = player.hp;
    const maxHp = player.max_hp;
    const hpPct = Math.max(0, (hp / maxHp) * 100);

    document.getElementById('combat-char-icon').textContent = player.character_icon || '⚔️';
    document.getElementById('combat-player-name').textContent = player.character_name || '英雄';
    document.getElementById('combat-hp').textContent = `${hp}/${maxHp}`;
    document.getElementById('combat-block').textContent = player.block || 0;

    const fill = document.getElementById('combat-hp-fill');
    fill.style.width = hpPct + '%';
    fill.className = 'hp-fill' + (hpPct <= 30 ? ' low' : hpPct <= 60 ? ' mid' : '');

    // 状态效果
    const effects = document.getElementById('combat-status-effects');
    effects.innerHTML = [
      player.strength > 0 ? `<span class="status-badge strength">💪 ${player.strength}</span>` : '',
      player.dexterity > 0 ? `<span class="status-badge dexterity">🤸 ${player.dexterity}</span>` : '',
      player.weak_turns > 0 ? `<span class="status-badge weak">💔 弱${player.weak_turns}</span>` : '',
      player.vulnerable_turns > 0 ? `<span class="status-badge vulnerable">⬇️ 易伤${player.vulnerable_turns}</span>` : '',
    ].filter(Boolean).join('');
  },

  renderHand(hand, energy, onPlay) {
    const container = document.getElementById('hand-cards');
    container.innerHTML = '';

    hand.forEach((card, idx) => {
      const el = this.createCardElement(card, false);
      const cost = card.cost;
      const canPlay = typeof cost === 'number' && energy >= cost && !card.unplayable;
      if (!canPlay) el.classList.add('disabled');

      el.addEventListener('click', () => {
        if (canPlay) onPlay(idx);
        else UI.notify('能量不足或无法打出此牌', 'warning');
      });

      container.appendChild(el);
    });
  },

  createCardElement(card, large = false) {
    const el = document.createElement('div');
    el.className = `card ${card.type || 'skill'}${large ? ' large' : ''}`;
    if (card.upgraded) el.classList.add('upgraded');

    // Hover tooltip
    el.addEventListener('mouseenter', (e) => UI._showCardTooltip(card, e));
    el.addEventListener('mousemove', (e) => UI._moveCardTooltip(e));
    el.addEventListener('mouseleave', () => UI._hideCardTooltip());

    const costVal = card.cost;
    const costClass = costVal === 0 ? 'zero' : '';
    const costDisplay = typeof costVal === 'number' ? costVal : 'X';

    let bodyContent = '';
    if (card.damage > 0) {
      bodyContent += `<div class="card-damage">⚔️${card.damage * (card.hits || 1) > card.damage ? card.hits + 'x' : ''}${card.damage}</div>`;
    }
    if (card.block > 0) {
      bodyContent += `<div class="card-block-val">🛡️${card.block}</div>`;
    }
    if (card.poison_stacks > 0) {
      bodyContent += `<div style="color:#8e44ad">☠️${card.poison_stacks}</div>`;
    }
    if (card.draw > 0) {
      bodyContent += `<div style="color:#3498db">📖+${card.draw}</div>`;
    }
    if (card.strength_gain > 0) {
      bodyContent += `<div style="color:#e74c3c">💪+${card.strength_gain}</div>`;
    }

    const typeLabels = { attack: '攻击', skill: '技能', power: '能力', curse: '诅咒', status: '状态' };

    el.innerHTML = `
      <div class="card-cost ${costClass}">${costDisplay}</div>
      ${card.upgraded ? '<span class="card-upgraded">★</span>' : ''}
      <div class="card-name">${card.name}</div>
      <div class="card-type-label">${typeLabels[card.type] || '?'}</div>
      <div class="card-body">
        ${bodyContent}
        <div class="card-desc">${card.description || ''}</div>
      </div>
      ${card.exhaust ? '<div class="card-exhaust">耗尽</div>' : ''}
    `;

    return el;
  },

  // ===== 药水栏 =====
  renderPotions(potions, onUse) {
    const bar = document.getElementById('potions-bar');
    if (!bar) return;
    bar.innerHTML = '';
    (potions || []).forEach((potion, idx) => {
      const btn = document.createElement('button');
      btn.className = 'potion-btn';
      btn.innerHTML = `
        ${potion.icon || '🧪'}
        <span class="potion-tooltip">${potion.name}<br>${potion.description}</span>
      `;
      btn.title = `${potion.name}: ${potion.description}`;
      btn.addEventListener('click', () => onUse(idx));
      bar.appendChild(btn);
    });
  },

  // ===== 战斗日志 =====
  appendLog(logs) {
    if (!logs || !logs.length) return;
    const content = document.getElementById('log-content');
    logs.forEach(log => {
      const entry = document.createElement('div');
      entry.className = 'log-entry ' + _logClass(log);
      entry.textContent = log;
      content.insertBefore(entry, content.firstChild);
    });
  },

  clearLog() {
    const content = document.getElementById('log-content');
    if (content) content.innerHTML = '';
  },

  // ===== 卡牌奖励 =====
  renderCardRewards(cards, onPick) {
    const container = document.getElementById('reward-cards');
    container.innerHTML = '';
    cards.forEach(card => {
      const wrapper = document.createElement('div');
      wrapper.className = 'reward-card-wrapper';
      const cardEl = this.createCardElement(card, true);
      const btn = document.createElement('button');
      btn.className = 'btn btn-primary';
      btn.textContent = '选择此牌';
      btn.addEventListener('click', () => onPick(card.id));
      wrapper.appendChild(cardEl);
      wrapper.appendChild(btn);
      container.appendChild(wrapper);
    });
  },

  // ===== Boss遗物选择 =====
  renderBossRelics(relics, onPick) {
    const container = document.getElementById('boss-relic-choices');
    container.innerHTML = '';
    relics.forEach(relic => {
      const el = document.createElement('div');
      el.className = 'relic-choice';
      el.innerHTML = `
        <div class="relic-choice-icon">💎</div>
        <div class="relic-choice-name">${relic.name}</div>
        <div class="relic-choice-desc">${relic.description}</div>
      `;
      el.addEventListener('click', () => onPick(relic.id));
      container.appendChild(el);
    });
  },

  // ===== 商店渲染 =====
  renderShop(shop, player, onBuyCard, onBuyRelic, onBuyPotion, onRemoveCard, onHeal) {
    if (!shop) return;

    document.getElementById('shop-gold').textContent = player.gold;

    // 卡牌
    const cardsEl = document.getElementById('shop-cards');
    cardsEl.innerHTML = '';
    (shop.cards || []).forEach(card => {
      const price = shop.card_prices[card.id] || 100;
      const canAfford = player.gold >= price;
      const item = document.createElement('div');
      item.className = 'shop-item';
      item.innerHTML = `
        <div class="shop-item-info">
          <div class="shop-item-name">${card.name} <small style="color:var(--text-dim)">[${card.type}]</small></div>
          <div class="shop-item-desc">${card.description}</div>
        </div>
        <button class="btn btn-gold" ${canAfford ? '' : 'disabled'} data-id="${card.id}">
          💰 ${price}
        </button>
      `;
      item.querySelector('button').addEventListener('click', () => onBuyCard(card.id));
      cardsEl.appendChild(item);
    });

    // 遗物
    const relicsEl = document.getElementById('shop-relics');
    relicsEl.innerHTML = '';
    (shop.relics || []).forEach(relic => {
      const price = shop.relic_prices[relic.id] || 200;
      const canAfford = player.gold >= price;
      const item = document.createElement('div');
      item.className = 'shop-item';
      item.innerHTML = `
        <div class="shop-item-info">
          <div class="shop-item-name">💎 ${relic.name}</div>
          <div class="shop-item-desc">${relic.description}</div>
        </div>
        <button class="btn btn-gold" ${canAfford ? '' : 'disabled'} data-id="${relic.id}">
          💰 ${price}
        </button>
      `;
      item.querySelector('button').addEventListener('click', () => onBuyRelic(relic.id));
      relicsEl.appendChild(item);
    });

    // 药水
    const potionsEl = document.getElementById('shop-potions');
    if (potionsEl) {
      potionsEl.innerHTML = '';
      (shop.potions || []).forEach(potion => {
        const price = potion.price || 50;
        const canAfford = player.gold >= price;
        const potionsFull = (player.potions || []).length >= 3;
        const item = document.createElement('div');
        item.className = 'shop-item';
        item.innerHTML = `
          <div class="shop-item-info">
            <div class="shop-item-name">${potion.icon} ${potion.name}</div>
            <div class="shop-item-desc">${potion.description}</div>
          </div>
          <button class="btn btn-secondary" ${(canAfford && !potionsFull) ? '' : 'disabled'}>
            💰 ${price}${potionsFull ? ' (满)' : ''}
          </button>
        `;
        item.querySelector('button').addEventListener('click', () => onBuyPotion(potion.id));
        potionsEl.appendChild(item);
      });
    }

    // 服务
    const servicesEl = document.getElementById('shop-services');
    servicesEl.innerHTML = '';

    const healPrice = shop.heal_price || 30;
    const removePrice = shop.remove_price || 75;

    const healItem = document.createElement('div');
    healItem.className = 'shop-item';
    healItem.innerHTML = `
      <div class="shop-item-info">
        <div class="shop-item-name">💊 治疗</div>
        <div class="shop-item-desc">恢复约${shop.heal_amount || 20}点HP</div>
      </div>
      <button class="btn btn-secondary" ${player.gold >= healPrice ? '' : 'disabled'}>💰 ${healPrice}</button>
    `;
    healItem.querySelector('button').addEventListener('click', onHeal);
    servicesEl.appendChild(healItem);

    const removeItem = document.createElement('div');
    removeItem.className = 'shop-item';
    removeItem.innerHTML = `
      <div class="shop-item-info">
        <div class="shop-item-name">🗑️ 移除卡牌</div>
        <div class="shop-item-desc">从牌组中永久移除一张牌</div>
      </div>
      <button class="btn btn-secondary" ${player.gold >= removePrice ? '' : 'disabled'}>💰 ${removePrice}</button>
    `;
    removeItem.querySelector('button').addEventListener('click', () => onRemoveCard(removePrice));
    servicesEl.appendChild(removeItem);
  },

  // ===== 休息点-升级选择 =====
  renderUpgradeDeck(deck, onUpgrade) {
    const container = document.getElementById('upgrade-deck-cards');
    container.innerHTML = '';
    const upgradeable = deck.filter(c => !c.upgraded && c.type !== 'curse' && c.type !== 'status');
    if (upgradeable.length === 0) {
      container.innerHTML = '<p style="color:var(--text-secondary)">没有可升级的卡牌</p>';
      return;
    }
    upgradeable.forEach(card => {
      const el = this.createCardElement(card, false);
      el.style.cursor = 'pointer';
      el.addEventListener('click', () => onUpgrade(card.id));
      container.appendChild(el);
    });
  },

  // ===== 事件渲染 =====
  renderEvent(event, onChoose) {
    if (!event) return;
    document.getElementById('event-image').textContent = event.image || '❓';
    document.getElementById('event-title').textContent = event.title || '神秘事件';
    document.getElementById('event-description').textContent = event.description || '';

    const choicesEl = document.getElementById('event-choices');
    choicesEl.innerHTML = '';
    (event.choices || []).forEach((choice, idx) => {
      const btn = document.createElement('button');
      btn.className = 'event-choice';
      btn.textContent = choice.text;
      btn.addEventListener('click', () => onChoose(idx));
      choicesEl.appendChild(btn);
    });
  },

  // ===== 排行榜 =====
  renderLeaderboard(entries, stats) {
    // 全局统计概览
    const statsEl = document.getElementById('leaderboard-stats');
    if (statsEl && stats) {
      statsEl.innerHTML = `
        <div class="lb-stat"><span>🎮 总对局</span><strong>${stats.total_runs || 0}</strong></div>
        <div class="lb-stat"><span>🏆 胜率</span><strong>${stats.win_rate || 0}%</strong></div>
        <div class="lb-stat"><span>🏔️ 最高层</span><strong>${stats.best_floor || 0}</strong></div>
        <div class="lb-stat"><span>👤 在线</span><strong>${stats.active_players || 0}</strong></div>
      `;
    }

    const container = document.getElementById('leaderboard-content');
    if (!container) return;

    if (!entries || entries.length === 0) {
      container.innerHTML = '<div class="loading">暂无记录。成为第一位上榜的英雄！</div>';
      return;
    }

    const medals = ['🥇', '🥈', '🥉'];
    container.innerHTML = `
      <table class="lb-table">
        <thead>
          <tr>
            <th>#</th><th>玩家</th><th>职业</th><th>天赋</th>
            <th>层数</th><th>击杀</th><th>结果</th><th>分数</th>
          </tr>
        </thead>
        <tbody>
          ${entries.map((e, i) => `
            <tr class="lb-row ${e.result === 'victory' ? 'lb-victory' : ''}">
              <td>${medals[i] || (i + 1)}</td>
              <td class="lb-name">${e.player_name}</td>
              <td>${e.character_icon} ${e.character}</td>
              <td>${e.ascension > 0 ? `⚡${e.ascension}` : '—'}</td>
              <td>${e.floor}</td>
              <td>${e.kills}</td>
              <td>${e.result === 'victory' ? '🏆 胜利' : '💀 失败'}</td>
              <td class="lb-score">${e.score.toLocaleString()}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  },

  // ===== 统计 =====
  renderStats(player, containerId, finalStats, ascensionName) {
    const container = document.getElementById(containerId);
    if (!container || !player) return;
    const s = finalStats || {};
    const floor = s.floor ?? player.floor ?? 0;
    const kills = s.kills ?? player.kills ?? 0;
    const turns = s.turns ?? player.turns ?? 0;
    const cardsPlayed = s.cards_played ?? player.cards_played ?? 0;
    const dmgDealt = s.damage_dealt ?? player.damage_dealt ?? 0;
    const dmgTaken = s.damage_taken ?? player.damage_taken ?? 0;
    const goldEarned = s.gold_earned ?? player.gold_earned ?? player.gold ?? 0;
    const relicsCount = s.relics_count ?? (player.relics || []).length;
    const deckSize = s.deck_size ?? (player.deck || []).length;
    const ascLabel = ascensionName || '普通模式';
    const ascLevel = s.ascension ?? 0;

    container.innerHTML = `
      <div class="stat-row"><span class="stat-label">职业</span><span class="stat-value">${player.character_icon || ''} ${player.character_name || s.character || ''}</span></div>
      <div class="stat-row"><span class="stat-label">难度</span><span class="stat-value ${ascLevel > 0 ? 'stat-highlight' : ''}">${ascLabel}${ascLevel > 0 ? ' ⚡' : ''}</span></div>
      <div class="stat-row"><span class="stat-label">到达层数</span><span class="stat-value">${floor}</span></div>
      <div class="stat-row"><span class="stat-label">击杀数</span><span class="stat-value">${kills}</span></div>
      <div class="stat-row"><span class="stat-label">战斗回合</span><span class="stat-value">${turns}</span></div>
      <div class="stat-row"><span class="stat-label">使用卡牌</span><span class="stat-value">${cardsPlayed}</span></div>
      <div class="stat-row"><span class="stat-label">造成伤害</span><span class="stat-value">${dmgDealt}</span></div>
      <div class="stat-row"><span class="stat-label">承受伤害</span><span class="stat-value">${dmgTaken}</span></div>
      <div class="stat-row"><span class="stat-label">获得金币</span><span class="stat-value">💰 ${goldEarned}</span></div>
      <div class="stat-row"><span class="stat-label">遗物数量</span><span class="stat-value">${relicsCount}</span></div>
      <div class="stat-row"><span class="stat-label">牌组大小</span><span class="stat-value">${deckSize}</span></div>
    `;
  },
  // ===== 卡牌 Tooltip =====
  _showCardTooltip(card, e) {
    const tip = document.getElementById('card-tooltip');
    if (!tip) return;
    const typeLabels = { attack: '攻击', skill: '技能', power: '能力', curse: '诅咒', status: '状态' };
    const rarityLabels = { starter: '基础', common: '普通', uncommon: '非普通', rare: '稀有', curse: '诅咒' };
    const rarityColors = { starter: '#9a7d5a', common: '#e8d5b0', uncommon: '#3498db', rare: '#f39c12', curse: '#888' };

    const costStr = typeof card.cost === 'number' ? `${card.cost}费` : 'X费';
    const rarityColor = rarityColors[card.rarity] || '#e8d5b0';
    const upgradedMark = card.upgraded ? ' <span style="color:#f39c12">★升级</span>' : '';

    let statsHtml = '';
    if (card.damage > 0) statsHtml += `<div>⚔️ 伤害：<strong>${card.damage}</strong>${card.hits > 1 ? ` ×${card.hits}` : ''}</div>`;
    if (card.block > 0) statsHtml += `<div>🛡️ 格挡：<strong>${card.block}</strong></div>`;
    if (card.poison_stacks > 0) statsHtml += `<div>☠️ 毒素：<strong>${card.poison_stacks}</strong></div>`;
    if (card.draw > 0) statsHtml += `<div>📖 抽牌：<strong>+${card.draw}</strong></div>`;
    if (card.strength_gain > 0) statsHtml += `<div>💪 力量：<strong>+${card.strength_gain}</strong></div>`;
    if (card.weak_turns > 0) statsHtml += `<div>💔 虚弱：<strong>${card.weak_turns}回合</strong></div>`;
    if (card.vulnerable_turns > 0) statsHtml += `<div>⬇️ 易伤：<strong>${card.vulnerable_turns}回合</strong></div>`;

    const flagsHtml = [
      card.exhaust ? '<span class="tip-flag exhaust">耗尽</span>' : '',
      card.ethereal ? '<span class="tip-flag ethereal">以太</span>' : '',
      card.innate ? '<span class="tip-flag innate">先手</span>' : '',
      card.retain ? '<span class="tip-flag retain">保留</span>' : '',
    ].filter(Boolean).join('');

    tip.innerHTML = `
      <div class="tip-header">
        <span class="tip-name">${card.name}${upgradedMark}</span>
        <span class="tip-cost">${costStr}</span>
      </div>
      <div class="tip-type" style="color:${rarityColor}">${typeLabels[card.type] || '?'} · ${rarityLabels[card.rarity] || ''}</div>
      ${statsHtml ? `<div class="tip-stats">${statsHtml}</div>` : ''}
      <div class="tip-desc">${card.description || ''}</div>
      ${flagsHtml ? `<div class="tip-flags">${flagsHtml}</div>` : ''}
    `;
    tip.classList.remove('hidden');
    this._moveCardTooltip(e);
  },

  _moveCardTooltip(e) {
    const tip = document.getElementById('card-tooltip');
    if (!tip || tip.classList.contains('hidden')) return;
    const margin = 14;
    const tw = tip.offsetWidth || 220;
    const th = tip.offsetHeight || 160;
    let x = e.clientX + margin;
    let y = e.clientY - th / 2;
    if (x + tw > window.innerWidth) x = e.clientX - tw - margin;
    if (y < 4) y = 4;
    if (y + th > window.innerHeight - 4) y = window.innerHeight - th - 4;
    tip.style.left = x + 'px';
    tip.style.top = y + 'px';
  },

  _hideCardTooltip() {
    const tip = document.getElementById('card-tooltip');
    if (tip) tip.classList.add('hidden');
  },
};

// 辅助函数
function _intentIcon(action) {
  const icons = { attack: '⚔️', block: '🛡️', buff: '⬆️', special: '✨', debuff: '⬇️' };
  return icons[action] || '❓';
}

function _logClass(log) {
  if (log.includes('伤害') || log.includes('攻击')) return 'damage';
  if (log.includes('恢复') || log.includes('治愈')) return 'heal';
  if (log.includes('格挡') || log.includes('防御')) return 'block';
  return 'info';
}
