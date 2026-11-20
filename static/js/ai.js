// ai.js - AI generation skeleton shimmer and rotating status messages
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('ai-generate-form');
  const formCard = document.getElementById('ai-form-card');
  const skeletonContainer = document.getElementById('ai-generating-skeleton');
  const rotatingTextEl = document.getElementById('ai-status-rotator');

  if (form && skeletonContainer) {
    form.addEventListener('submit', () => {
      // Switch view from form to skeleton
      if (formCard) formCard.style.display = 'none';
      skeletonContainer.style.display = 'block';

      // Rotating messages
      const messages = [
        'Reading your prompt...',
        'Synthesizing quiz domain & topics...',
        'Writing questions & 4 options...',
        'Checking answers & verifying accuracy...',
        'Formatting final preview...'
      ];
      let msgIdx = 0;

      setInterval(() => {
        msgIdx = (msgIdx + 1) % messages.length;
        if (rotatingTextEl) {
          rotatingTextEl.textContent = messages[msgIdx];
        }
      }, 2000);
    });
  }
});
