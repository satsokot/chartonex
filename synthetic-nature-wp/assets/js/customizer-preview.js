(function ($) {
  // Brand name
  wp.customize('sn_brand_name', function (value) {
    value.bind(function (v) {
      $('.sn-brand').text(v);
    });
  });

  // Hero title lines — rebuild char animation
  function rebuildTitle() {
    var line1 = wp.customize('sn_title_line1')();
    var line2 = wp.customize('sn_title_line2')();
    var el = document.querySelector('.sn-title');
    if (!el) return;
    var lines = el.querySelectorAll('.line');
    if (lines[0]) lines[0].setAttribute('data-text', line1);
    if (lines[1]) lines[1].setAttribute('data-text', line2);
    // Rebuild chars
    var globalIndex = 0;
    lines.forEach(function (line) {
      var text = line.getAttribute('data-text') || '';
      line.innerHTML = '';
      for (var i = 0; i < text.length; i++) {
        var span = document.createElement('span');
        span.className = 'sn-char' + (text[i] === ' ' ? ' space' : '');
        span.textContent = text[i];
        span.style.animationDelay = (globalIndex * 0.07) + 's';
        line.appendChild(span);
        globalIndex++;
      }
    });
  }

  wp.customize('sn_title_line1', function (value) {
    value.bind(rebuildTitle);
  });
  wp.customize('sn_title_line2', function (value) {
    value.bind(rebuildTitle);
  });

  // Subtitle
  wp.customize('sn_subtitle', function (value) {
    value.bind(function (v) {
      $('.sn-subtitle').html(v);
    });
  });

  // CTA text
  wp.customize('sn_cta_text', function (value) {
    value.bind(function (v) {
      $('.sn-cta').text(v);
    });
  });

})(jQuery);
