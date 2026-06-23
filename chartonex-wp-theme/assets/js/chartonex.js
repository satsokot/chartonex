/* ============================================
   Chartonex — Main JS
   ============================================ */
(function () {
  'use strict';

  /* ── Navbar scroll state ── */
  const nav = document.querySelector('.cx-nav');
  if (nav) {
    const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ── Mobile menu ── */
  const hamburger  = document.querySelector('.cx-hamburger');
  const mobileMenu = document.querySelector('.cx-mobile-menu');
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      const open = mobileMenu.style.display === 'block';
      mobileMenu.style.display = open ? 'none' : 'block';
      hamburger.innerHTML = open
        ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>'
        : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    });
    mobileMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        mobileMenu.style.display = 'none';
        hamburger.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
      });
    });
  }

  /* ── Intersection Observer — fade-in on scroll ── */
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );
  document.querySelectorAll('.cx-animate-observe').forEach(el => observer.observe(el));

  /* ── Animated counter ── */
  function animateCounter(el) {
    const target = parseFloat(el.dataset.target);
    const suffix = el.dataset.suffix || '';
    const prefix = el.dataset.prefix || '';
    const duration = 2000;
    const start = performance.now();
    const isDecimal = target % 1 !== 0;

    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = target * ease;
      el.textContent = prefix + (isDecimal ? current.toFixed(1) : Math.floor(current).toLocaleString()) + suffix;
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  const counterObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.5 }
  );
  document.querySelectorAll('.cx-stat-num[data-target]').forEach(el => counterObserver.observe(el));

  /* ── Live ticker prices (demo animation) ── */
  const tickers = [
    { sym: 'BTC/USDT', base: 68420, variance: 200, decimals: 0 },
    { sym: 'ETH/USDT', base: 3847,  variance: 40,  decimals: 0 },
    { sym: 'XAU/USD',  base: 2318,  variance: 8,   decimals: 2 },
  ];

  function randomWalk(base, variance) {
    return base + (Math.random() - 0.5) * variance;
  }

  const tickerEls = {
    price: document.querySelector('.cx-chart-price'),
    change: document.querySelector('.cx-chart-change'),
  };
  const tickerRows = document.querySelectorAll('.cx-ticker-card');

  let prices = tickers.map(t => t.base);

  function updateTickers() {
    tickers.forEach((t, i) => {
      const prev = prices[i];
      const next = randomWalk(t.base, t.variance);
      prices[i] = next;
      const pct = ((next - t.base) / t.base * 100).toFixed(2);
      const isUp = next >= prev;

      if (i === 0 && tickerEls.price) {
        tickerEls.price.textContent = '$' + next.toLocaleString('en-US', { maximumFractionDigits: t.decimals });
        tickerEls.change.textContent = (pct >= 0 ? '+' : '') + pct + '%';
        tickerEls.change.style.color = pct >= 0 ? '#4ADE80' : '#F87171';
        tickerEls.change.style.background = pct >= 0 ? 'rgba(74,222,128,.12)' : 'rgba(248,113,113,.12)';
      }

      if (tickerRows[i]) {
        const valEl = tickerRows[i].querySelector('.cx-ticker-val');
        const chgEl = tickerRows[i].querySelector('.cx-ticker-chg');
        if (valEl) {
          valEl.textContent = (t.sym === 'XAU/USD' ? '$' : '$') + next.toLocaleString('en-US', { maximumFractionDigits: t.decimals });
          valEl.style.color = isUp ? '#4ADE80' : '#F87171';
          setTimeout(() => { valEl.style.color = ''; }, 400);
        }
        if (chgEl) {
          chgEl.textContent = (pct >= 0 ? '+' : '') + pct + '%';
          chgEl.className = 'cx-ticker-chg ' + (pct >= 0 ? 'up' : 'down');
        }
      }
    });
  }

  setInterval(updateTickers, 2000);

  /* ── Animated SVG chart path ── */
  function buildChartPath() {
    const svg = document.querySelector('.cx-chart-svg');
    if (!svg) return;

    const W = svg.viewBox.baseVal.width || 500;
    const H = svg.viewBox.baseVal.height || 180;

    // Generate a realistic-looking price path
    const points = [];
    const count = 30;
    let y = H * 0.65;
    for (let i = 0; i < count; i++) {
      const x = (i / (count - 1)) * W;
      y = Math.max(H * 0.15, Math.min(H * 0.85, y + (Math.random() - 0.42) * 18));
      points.push({ x, y });
    }

    // Smooth curve
    function catmullRom(pts) {
      if (pts.length < 2) return '';
      let d = `M ${pts[0].x},${pts[0].y}`;
      for (let i = 0; i < pts.length - 1; i++) {
        const p0 = pts[Math.max(0, i - 1)];
        const p1 = pts[i];
        const p2 = pts[i + 1];
        const p3 = pts[Math.min(pts.length - 1, i + 2)];
        const cp1x = p1.x + (p2.x - p0.x) / 6;
        const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6;
        const cp2y = p2.y - (p3.y - p1.y) / 6;
        d += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`;
      }
      return d;
    }

    const path = catmullRom(points);
    const last = points[points.length - 1];

    // Area fill
    const areaPath = path + ` L ${last.x},${H} L 0,${H} Z`;

    const defs = svg.querySelector('defs') || svg.insertBefore(document.createElementNS('http://www.w3.org/2000/svg', 'defs'), svg.firstChild);
    defs.innerHTML = `
      <linearGradient id="chartGrad" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#A855F7"/>
        <stop offset="100%" stop-color="#22D3EE"/>
      </linearGradient>
      <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#A855F7" stop-opacity="0.25"/>
        <stop offset="100%" stop-color="#22D3EE" stop-opacity="0"/>
      </linearGradient>
    `;

    // Area
    const area = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    area.setAttribute('d', areaPath);
    area.setAttribute('fill', 'url(#areaGrad)');
    svg.appendChild(area);

    // Line
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    line.setAttribute('d', path);
    line.setAttribute('stroke', 'url(#chartGrad)');
    line.setAttribute('stroke-width', '2.5');
    line.setAttribute('fill', 'none');
    line.setAttribute('stroke-linecap', 'round');
    line.classList.add('cx-chart-line');

    // Calculate total length for dasharray
    svg.appendChild(line);
    const len = line.getTotalLength();
    line.style.strokeDasharray = len;
    line.style.strokeDashoffset = len;
    line.style.animation = `drawLine 2.5s 0.5s ease forwards`;

    // End dot
    const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dot.setAttribute('cx', last.x);
    dot.setAttribute('cy', last.y);
    dot.setAttribute('r', '5');
    dot.setAttribute('fill', '#22D3EE');
    dot.style.animation = 'pulse 2s ease-in-out infinite';
    dot.style.filter = 'drop-shadow(0 0 6px #22D3EE)';
    svg.appendChild(dot);

    // Horizontal grid lines
    [0.25, 0.5, 0.75].forEach(frac => {
      const y = H * frac;
      const gridLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      gridLine.setAttribute('x1', 0); gridLine.setAttribute('y1', y);
      gridLine.setAttribute('x2', W); gridLine.setAttribute('y2', y);
      gridLine.setAttribute('stroke', 'rgba(255,255,255,0.05)');
      gridLine.setAttribute('stroke-width', '1');
      svg.insertBefore(gridLine, area);
    });
  }

  buildChartPath();

})();
