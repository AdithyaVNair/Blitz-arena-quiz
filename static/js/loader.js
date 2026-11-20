// loader.js - Button spinner and submission disabling
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        // Prevent double submissions
        submitBtn.disabled = true;
        
        // Add spinner if not already present
        const originalText = submitBtn.innerHTML;
        const spinner = document.createElement('span');
        spinner.className = 'spinner';
        spinner.style.marginRight = '8px';
        submitBtn.prepend(spinner);
        
        // If form fails or page remains, reset after 10s fallback
        setTimeout(() => {
          submitBtn.disabled = false;
          if (spinner.parentNode) {
            spinner.parentNode.removeChild(spinner);
          }
        }, 10000);
      }
    });
  });
});

