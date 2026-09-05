// ConnectHub - Main JS (HTML5 + Tailwind frontend)
// Dark mode toggle: <html class="dark"> + Tailwind dark: variants
(function () {
  const toggle = document.getElementById('dark-toggle');
  const root = document.documentElement;
  const saved = localStorage.getItem('dark');
  if (saved === '1') {
    root.classList.add('dark');
    if (toggle) toggle.textContent = '☀️ Light';
  }
  if (toggle) {
    toggle.addEventListener('click', () => {
      root.classList.toggle('dark');
      const isDark = root.classList.contains('dark');
      localStorage.setItem('dark', isDark ? '1' : '0');
      toggle.textContent = isDark ? '☀️ Light' : '🌙 Dark';
    });
  }
  // Alerts auto-hide after 4s
  setTimeout(() => document.querySelectorAll('.alert').forEach(a => { a.style.display = 'none'; }), 4000);
})();

// Shared CSRF helper for AJAX (like/comment/chat polling)
function getCSRF() {
  return document.querySelector('[name=csrfmiddlewaretoken]')?.value
    || (document.cookie.match(/csrftoken=([^;]+)/) || [])[1]
    || '';
}
