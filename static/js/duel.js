// duel.js - 1v1 matchmaking controller
document.addEventListener('DOMContentLoaded', () => {
  const findBtn = document.getElementById('find-opponent-btn');
  const cancelBtn = document.getElementById('cancel-matchmaking-btn');
  const matchmakingStatus = document.getElementById('matchmaking-active');
  const matchmakingIdle = document.getElementById('matchmaking-idle');
  const elapsedText = document.getElementById('elapsed-seconds');
  const quizSelect = document.getElementById('duel-quiz-select');

  let pollInterval = null;
  let timerInterval = null;
  let elapsed = 0;

  function getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  }

  if (findBtn) {
    findBtn.addEventListener('click', () => {
      findBtn.disabled = true;
      const quizId = quizSelect ? quizSelect.value : '';

      const formData = new FormData();
      if (quizId) formData.append('quiz_id', quizId);

      fetch('/rooms/duel/find/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
        },
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'matched') {
          window.location.href = `/rooms/${data.room_code}/`;
        } else {
          startWaitingUI();
        }
      })
      .catch(err => {
        console.error('Matchmaking error:', err);
        findBtn.disabled = false;
      });
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      cancelBtn.disabled = true;
      fetch('/rooms/duel/cancel/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
        }
      })
      .then(() => {
        stopWaitingUI();
      })
      .catch(err => {
        console.error('Cancel error:', err);
        stopWaitingUI();
      });
    });
  }

  function startWaitingUI() {
    if (matchmakingIdle) matchmakingIdle.style.display = 'none';
    if (matchmakingStatus) matchmakingStatus.style.display = 'block';

    elapsed = 0;
    if (elapsedText) elapsedText.textContent = '0s';

    timerInterval = setInterval(() => {
      elapsed++;
      if (elapsedText) elapsedText.textContent = `${elapsed}s`;
    }, 1000);

    pollInterval = setInterval(() => {
      fetch('/rooms/duel/poll/')
        .then(res => res.json())
        .then(data => {
          if (data.status === 'matched') {
            clearInterval(pollInterval);
            clearInterval(timerInterval);
            window.location.href = `/rooms/${data.room_code}/`;
          }
        })
        .catch(console.error);
    }, 1500);
  }

  function stopWaitingUI() {
    clearInterval(pollInterval);
    clearInterval(timerInterval);
    if (matchmakingStatus) matchmakingStatus.style.display = 'none';
    if (matchmakingIdle) matchmakingIdle.style.display = 'block';
    if (findBtn) findBtn.disabled = false;
    if (cancelBtn) cancelBtn.disabled = false;
  }
});
