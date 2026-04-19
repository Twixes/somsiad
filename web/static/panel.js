// Sidebar toggle for mobile
document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.querySelector('.sidebar-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      document.body.classList.toggle('sidebar-open');
    });
  }

  // Close sidebar when clicking overlay
  var overlay = document.createElement('div');
  overlay.className = 'sidebar-overlay';
  document.body.appendChild(overlay);
  overlay.addEventListener('click', function () {
    document.body.classList.remove('sidebar-open');
  });

  // Auto-dismiss flash messages
  var flashes = document.querySelectorAll('.flash');
  for (var i = 0; i < flashes.length; i++) {
    (function (el) {
      setTimeout(function () {
        el.style.opacity = '0';
        el.style.transform = 'translateY(-8px)';
        setTimeout(function () { el.remove(); }, 300);
      }, 4000);
    })(flashes[i]);
  }
});

// Floating emojis on login page
(function () {
  var bg = document.getElementById('loginBg');
  if (!bg) return;

  var emojis = [
    '\ud83d\udc1c', '\ud83d\udd25', '\ud83d\udc38', '\ud83d\udca5', '\ud83d\udc07',
    '\ud83e\udd85', '\ud83e\udd16', '\ud83d\udc27', '\ud83c\udf08', '\ud83d\ude80',
    '\ud83c\udf89', '\ud83d\udca1', '\ud83c\udfaf', '\ud83c\udf55', '\ud83c\udf6a',
    '\ud83e\udd54', '\u2728', '\ud83d\udc3b', '\ud83c\udfb7', '\ud83d\udc7e'
  ];

  function spawn(delay) {
    var el = document.createElement('div');
    el.className = 'floating-emoji';
    el.textContent = emojis[Math.floor(Math.random() * emojis.length)];
    el.style.left = Math.random() * 100 + '%';
    el.style.animationDuration = (10 + Math.random() * 14) + 's';
    if (delay) el.style.animationDelay = delay + 's';
    el.style.fontSize = (1 + Math.random() * 1.2) + 'rem';
    bg.appendChild(el);
    el.addEventListener('animationend', function () { el.remove(); });
  }

  for (var i = 0; i < 12; i++) spawn(Math.random() * 8);

  setInterval(spawn, 2500);
})();
