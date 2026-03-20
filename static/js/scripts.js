// ── Flash message auto-dismiss ──
document.addEventListener('DOMContentLoaded', () => {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 3000);
  });
});

// ── Form validation ──
document.addEventListener('DOMContentLoaded', () => {
  const forms = document.querySelectorAll('form');

  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const inputs = form.querySelectorAll('input[type="text"], input[type="password"]');
      let valid = true;

      inputs.forEach(input => {
        if (!input.value.trim()) {
          valid = false;
          input.style.borderColor = '#e94560';
        } else {
          input.style.borderColor = '';
        }
      });

      if (!valid) {
        e.preventDefault();
        showError(form, 'Please fill in all fields.');
      }
    });
  });
});

function showError(form, message) {
  // Remove any existing error
  const existing = form.querySelector('.form-error');
  if (existing) existing.remove();

  const err = document.createElement('p');
  err.className = 'flash form-error';
  err.textContent = message;
  form.prepend(err);
}

// ── Match result badge colour (history page) ──
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.match-card').forEach(card => {
    const badge = card.querySelector('.result-badge');
    if (badge) {
      const result = badge.textContent.trim().toLowerCase();
      card.classList.add(result);    // adds .win or .loss for border colour
      badge.classList.add(result);   // colours the badge itself
    }
  });
});
