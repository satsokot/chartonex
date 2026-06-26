(function () {
  'use strict';

  /* ── Hamburger toggle ── */
  var btn = document.getElementById('sn-hamburger');
  var menu = document.getElementById('sn-mobile-menu');
  var iconMenu = document.getElementById('sn-icon-menu');
  var iconClose = document.getElementById('sn-icon-close');

  if (btn && menu) {
    btn.addEventListener('click', function () {
      var open = menu.classList.toggle('is-open');
      iconMenu.style.display  = open ? 'none'   : 'block';
      iconClose.style.display = open ? 'block'  : 'none';
      btn.setAttribute('aria-expanded', open);
    });

    // Close menu on link click
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        menu.classList.remove('is-open');
        iconMenu.style.display  = 'block';
        iconClose.style.display = 'none';
        btn.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ── Staggered char fade-in ── */
  function animateChars(selector, baseDelay, charDelay) {
    var el = document.querySelector(selector);
    if (!el) return;

    var lines = el.querySelectorAll('.line');
    var globalIndex = 0;

    lines.forEach(function (line) {
      var text = line.getAttribute('data-text') || '';
      line.innerHTML = '';

      for (var i = 0; i < text.length; i++) {
        var span = document.createElement('span');
        span.className = 'sn-char' + (text[i] === ' ' ? ' space' : '');
        span.textContent = text[i];
        span.style.animationDelay = (baseDelay + globalIndex * charDelay) + 's';
        line.appendChild(span);
        globalIndex++;
      }
    });
  }

  animateChars('.sn-title', 0, 0.07);

})();
