// room.js - Lobby + Game loop UI controller
document.addEventListener('DOMContentLoaded', () => {
  const roomDataEl = document.getElementById('room-meta');
  if (!roomDataEl) return;

  const roomCode = roomDataEl.dataset.roomCode;
  const roomMode = roomDataEl.dataset.roomMode || 'standard';
  const isHost = roomDataEl.dataset.isHost === 'true';
  const currentUsername = roomDataEl.dataset.username;

  // ── Apply dynamic cosmic theme based on room mode ──────────────
  _applyTheme(roomMode);

  // DOM Elements
  const lobbyView = document.getElementById('lobby-view');
  const gameView = document.getElementById('game-view');
  const finishedView = document.getElementById('finished-view');

  const playerRoster = document.getElementById('player-roster');
  const playerCount = document.getElementById('player-count');
  const startBtn = document.getElementById('start-game-btn');
  const waitingNotice = document.getElementById('waiting-notice');

  const questionIndexEl = document.getElementById('question-index');
  const questionTotalEl = document.getElementById('question-total');
  const questionTextEl = document.getElementById('question-text');
  const timerBar = document.getElementById('timer-bar');
  const timerRemainingText = document.getElementById('timer-remaining-text');
  const optionsGrid = document.getElementById('options-grid');
  const scoresRoster = document.getElementById('live-scores-roster');
  const finalLeaderboard = document.getElementById('final-leaderboard');
  const duelMascots = document.getElementById('duel-mascots');

  let timerInterval = null;
  let hasAnsweredCurrentQuestion = false;

  // Initialize WebSocket connection
  const socket = new BlitzSocket(`/ws/room/${roomCode}/`);

  // 1. Lobby State Handler
  socket.on('lobby_state', (data) => {
    if (lobbyView) lobbyView.style.display = 'block';
    if (gameView) gameView.style.display = 'none';
    if (finishedView) finishedView.style.display = 'none';

    if (playerCount) playerCount.textContent = data.players.length;
    if (playerRoster) {
      playerRoster.innerHTML = '';
      data.players.forEach(p => {
        const item = document.createElement('div');
        item.className = 'player-chip';
        item.innerHTML = `<span class="player-avatar">${getAvatarEmoji(p.avatar)}</span> <span class="player-name">${escapeHtml(p.name)}</span>`;
        playerRoster.appendChild(item);
      });
    }

    if (isHost && startBtn) {
      startBtn.style.display = 'inline-flex';
    } else if (waitingNotice) {
      waitingNotice.style.display = 'flex';
    }

    // Update duel mascot names if in duel mode
    if (roomMode === 'duel' && data.players.length >= 2) {
      const p1 = document.getElementById('duel-p1-name');
      const p2 = document.getElementById('duel-p2-name');
      if (p1) p1.textContent = data.players[0].name;
      if (p2) p2.textContent = data.players[1] ? data.players[1].name : 'Opponent';
    }
  });

  // Host clicks Start
  if (startBtn) {
    startBtn.addEventListener('click', () => {
      startBtn.disabled = true;
      socket.send({ type: 'start' });
    });
  }

  // 2. Question State Handler
  socket.on('question', (data) => {
    hasAnsweredCurrentQuestion = false;
    clearInterval(timerInterval);

    if (lobbyView) lobbyView.style.display = 'none';
    if (gameView) gameView.style.display = 'block';
    if (finishedView) finishedView.style.display = 'none';

    // Show duel mascots in duel mode
    if (duelMascots && roomMode === 'duel') {
      duelMascots.style.display = 'flex';
    }

    if (questionIndexEl) questionIndexEl.textContent = data.index;
    if (questionTotalEl) questionTotalEl.textContent = data.total;
    if (questionTextEl) questionTextEl.textContent = data.text;

    // Reset and start Question Timer Bar
    startTimer(data.time_limit);

    // Render Options
    if (optionsGrid) {
      optionsGrid.innerHTML = '';
      const letters = ['A', 'B', 'C', 'D'];
      const optClasses = ['option-a', 'option-b', 'option-c', 'option-d'];

      data.options.forEach((opt, idx) => {
        const btn = document.createElement('button');
        btn.className = `option-btn ${optClasses[idx % 4]}`;
        btn.dataset.optionId = opt.id;
        btn.innerHTML = `
          <span class="option-badge">${letters[idx % 4]}</span>
          <span class="option-text">${escapeHtml(opt.text)}</span>
        `;

        btn.addEventListener('click', () => {
          if (hasAnsweredCurrentQuestion) return;
          hasAnsweredCurrentQuestion = true;

          btn.classList.add('selected');
          document.querySelectorAll('.option-btn').forEach(b => b.disabled = true);

          socket.send({
            type: 'answer',
            option_id: opt.id
          });
        });

        optionsGrid.appendChild(btn);
      });
    }
  });

  // 3. Reveal State Handler
  socket.on('reveal', (data) => {
    clearInterval(timerInterval);
    if (timerBar) timerBar.style.width = '0%';

    const correctId = data.correct_option_id;
    document.querySelectorAll('.option-btn').forEach(btn => {
      btn.disabled = true;
      if (parseInt(btn.dataset.optionId) === correctId) {
        btn.classList.add('correct');
      } else {
        btn.classList.add('wrong');
      }
    });

    // Update live scores
    if (scoresRoster && data.scores) {
      scoresRoster.innerHTML = '';
      data.scores.forEach(s => {
        const row = document.createElement('div');
        row.className = 'score-item';
        const deltaText = s.delta > 0 ? `+${s.delta}` : '+0';
        row.innerHTML = `
          <span class="score-player">${getAvatarEmoji(s.avatar)} ${escapeHtml(s.name)}</span>
          <span class="score-delta ${s.delta > 0 ? 'score-positive' : ''}">${deltaText}</span>
          <span class="score-total">${s.score} pts</span>
        `;
        scoresRoster.appendChild(row);
      });
    }
  });

  // 4. Finished State Handler
  socket.on('finished', (data) => {
    clearInterval(timerInterval);
    if (lobbyView) lobbyView.style.display = 'none';
    if (gameView) gameView.style.display = 'none';
    if (finishedView) finishedView.style.display = 'block';

    // Remove theme on finish
    document.body.classList.remove('theme-duel', 'theme-blitz', 'theme-solo');

    if (finalLeaderboard && data.scores) {
      finalLeaderboard.innerHTML = '';
      data.scores.forEach((s, idx) => {
        const card = document.createElement('div');
        card.className = `card podium-card rank-${idx + 1}`;
        card.innerHTML = `
          <div class="podium-rank">#${idx + 1}</div>
          <div class="podium-info">
            <span class="podium-name">${getAvatarEmoji(s.avatar)} ${escapeHtml(s.name)}</span>
            <span class="podium-score" data-target="${s.score}">0 pts</span>
          </div>
        `;
        finalLeaderboard.appendChild(card);
      });

      animateScores();
    }
  });

  // ── Timer Animation Helper ───────────────────────────────────
  function startTimer(durationSec) {
    if (!timerBar) return;
    timerBar.classList.remove('urgent');
    timerBar.style.width = '100%';

    let remaining = durationSec;
    if (timerRemainingText) timerRemainingText.textContent = `${remaining}s`;

    const stepMs = 100;
    const totalMs = durationSec * 1000;
    let elapsedMs = 0;

    timerInterval = setInterval(() => {
      elapsedMs += stepMs;
      const pct = Math.max(0, 100 - (elapsedMs / totalMs) * 100);
      timerBar.style.width = `${pct}%`;

      const secLeft = Math.ceil((totalMs - elapsedMs) / 1000);
      if (timerRemainingText) timerRemainingText.textContent = `${secLeft}s`;

      if (secLeft <= 5) {
        timerBar.classList.add('urgent');
      }

      if (elapsedMs >= totalMs) {
        clearInterval(timerInterval);
      }
    }, stepMs);
  }

  // Count-up numbers (respecting prefers-reduced-motion)
  function animateScores() {
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    document.querySelectorAll('.podium-score').forEach(el => {
      const target = parseInt(el.dataset.target) || 0;
      if (prefersReduced) {
        el.textContent = `${target} pts`;
        return;
      }
      let current = 0;
      const step = Math.max(1, Math.floor(target / 40));
      const interval = setInterval(() => {
        current = Math.min(target, current + step);
        el.textContent = `${current} pts`;
        if (current >= target) clearInterval(interval);
      }, 25);
    });
  }

  // ── Dynamic theme engine ─────────────────────────────────────
  function _applyTheme(mode) {
    document.body.classList.remove('theme-solo', 'theme-duel', 'theme-blitz');
    const duelBg = document.querySelector('.duel-arena-bg');

    if (mode === 'duel') {
      document.body.classList.add('theme-duel');
      if (duelBg) duelBg.style.display = 'block';
    } else if (mode === 'blitz') {
      document.body.classList.add('theme-blitz');
    } else {
      document.body.classList.add('theme-solo');
    }
  }

  function getAvatarEmoji(avatar) {
    const map = { fox: '🦊', knight: '⚔️', owl: '🦉', bear: '🐻', bot: '🤖' };
    return map[avatar] || '🎮';
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.innerText = str;
    return div.innerHTML;
  }
});
