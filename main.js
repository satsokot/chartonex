/* ============================================================
   NEXUS — DIGITAL UNIVERSE  |  main.js
   ============================================================ */

'use strict';

/* ── helpers ── */
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const rand = (a, b) => Math.random() * (b - a) + a;
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);

/* ════════════════════════════════════
   LOADER
   ════════════════════════════════════ */
function initLoader() {
  const loader = $('#loader');
  const percentEl = $('.loader-percent');
  let progress = 0;
  const tick = setInterval(() => {
    progress = Math.min(100, progress + Math.random() * 6);
    percentEl.textContent = Math.floor(progress) + '%';
    if (progress >= 100) {
      clearInterval(tick);
      setTimeout(() => {
        loader.classList.add('hidden');
        startAnimations();
      }, 400);
    }
  }, 40);
}

/* ════════════════════════════════════
   CUSTOM CURSOR
   ════════════════════════════════════ */
function initCursor() {
  const dot  = $('#cursor-dot');
  const ring = $('#cursor-ring');
  const trailContainer = $('#cursor-trail-container');
  let mx = 0, my = 0, rx = 0, ry = 0;
  let lastTrail = 0;

  document.addEventListener('mousemove', (e) => {
    mx = e.clientX; my = e.clientY;
    dot.style.left  = mx + 'px';
    dot.style.top   = my + 'px';

    /* trail */
    const now = Date.now();
    if (now - lastTrail > 40) {
      lastTrail = now;
      const t = document.createElement('div');
      t.className = 'cursor-trail';
      t.style.left = mx + 'px';
      t.style.top  = my + 'px';
      trailContainer.appendChild(t);
      setTimeout(() => t.remove(), 600);
    }
  });

  /* smooth ring follow */
  (function animRing() {
    rx = lerp(rx, mx, 0.12);
    ry = lerp(ry, my, 0.12);
    ring.style.left = rx + 'px';
    ring.style.top  = ry + 'px';
    requestAnimationFrame(animRing);
  })();

  /* hover effects */
  const interactables = 'a, button, .holo-card, .tl-card, input';
  document.querySelectorAll(interactables).forEach(el => {
    el.addEventListener('mouseenter', () => ring.classList.add('hover'));
    el.addEventListener('mouseleave', () => ring.classList.remove('hover'));
  });
}

/* ════════════════════════════════════
   PARTICLE BACKGROUND (THREE.JS)
   ════════════════════════════════════ */
function initParticleBackground() {
  const canvas = $('#bg-canvas');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.setSize(window.innerWidth, window.innerHeight);

  const scene  = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 5;

  /* ── star field ── */
  const starCount = 2000;
  const starGeo   = new THREE.BufferGeometry();
  const starPos   = new Float32Array(starCount * 3);
  const starSizes = new Float32Array(starCount);
  for (let i = 0; i < starCount; i++) {
    starPos[i * 3]     = rand(-50, 50);
    starPos[i * 3 + 1] = rand(-50, 50);
    starPos[i * 3 + 2] = rand(-50, 20);
    starSizes[i] = rand(0.5, 2.5);
  }
  starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
  starGeo.setAttribute('size',     new THREE.BufferAttribute(starSizes, 1));
  const starMat = new THREE.ShaderMaterial({
    uniforms: {
      time:  { value: 0 },
      color: { value: new THREE.Color(0x00f5ff) }
    },
    vertexShader: `
      attribute float size;
      uniform float time;
      varying float vAlpha;
      void main() {
        vAlpha = 0.4 + 0.4 * sin(time * 0.8 + position.x * 0.5);
        vec4 mvPos = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = size * (200.0 / -mvPos.z);
        gl_Position = projectionMatrix * mvPos;
      }
    `,
    fragmentShader: `
      uniform vec3 color;
      varying float vAlpha;
      void main() {
        float d = length(gl_PointCoord - vec2(0.5));
        if (d > 0.5) discard;
        float alpha = (1.0 - d * 2.0) * vAlpha;
        gl_FragColor = vec4(color, alpha);
      }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  scene.add(new THREE.Points(starGeo, starMat));

  /* ── floating particle system ── */
  const particleCount = 300;
  const pGeo  = new THREE.BufferGeometry();
  const pPos  = new Float32Array(particleCount * 3);
  const pVel  = new Float32Array(particleCount * 3);
  const pCol  = new Float32Array(particleCount * 3);
  const pSize = new Float32Array(particleCount);
  const colors = [
    new THREE.Color(0x00f5ff),
    new THREE.Color(0xa855f7),
    new THREE.Color(0xff006e),
    new THREE.Color(0x10b981),
  ];
  for (let i = 0; i < particleCount; i++) {
    pPos[i * 3]     = rand(-30, 30);
    pPos[i * 3 + 1] = rand(-20, 20);
    pPos[i * 3 + 2] = rand(-10, 5);
    pVel[i * 3]     = rand(-0.005, 0.005);
    pVel[i * 3 + 1] = rand(0.002, 0.01);
    pVel[i * 3 + 2] = 0;
    const c = colors[Math.floor(Math.random() * colors.length)];
    pCol[i * 3]     = c.r;
    pCol[i * 3 + 1] = c.g;
    pCol[i * 3 + 2] = c.b;
    pSize[i] = rand(1, 5);
  }
  pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
  pGeo.setAttribute('color',    new THREE.BufferAttribute(pCol, 3));
  pGeo.setAttribute('size',     new THREE.BufferAttribute(pSize, 1));
  const pMat = new THREE.ShaderMaterial({
    uniforms: { time: { value: 0 } },
    vertexShader: `
      attribute vec3 color;
      attribute float size;
      uniform float time;
      varying vec3 vColor;
      varying float vAlpha;
      void main() {
        vColor = color;
        vAlpha = 0.6 + 0.4 * sin(time + position.x);
        vec4 mvPos = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = size * (150.0 / -mvPos.z);
        gl_Position = projectionMatrix * mvPos;
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      varying float vAlpha;
      void main() {
        float d = length(gl_PointCoord - vec2(0.5));
        if (d > 0.5) discard;
        float alpha = (1.0 - d * 2.0) * vAlpha * 0.7;
        gl_FragColor = vec4(vColor, alpha);
      }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    vertexColors: true,
  });
  const particles = new THREE.Points(pGeo, pMat);
  scene.add(particles);

  /* ── grid plane ── */
  const gridGeo = new THREE.PlaneGeometry(80, 80, 30, 30);
  const gridMat = new THREE.ShaderMaterial({
    uniforms: { time: { value: 0 } },
    vertexShader: `
      uniform float time;
      varying vec2 vUv;
      void main() {
        vUv = uv;
        vec3 pos = position;
        pos.z = sin(pos.x * 0.3 + time * 0.5) * cos(pos.y * 0.3 + time * 0.4) * 0.5;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
      }
    `,
    fragmentShader: `
      varying vec2 vUv;
      void main() {
        float lx = step(0.97, fract(vUv.x * 30.0));
        float ly = step(0.97, fract(vUv.y * 30.0));
        float grid = max(lx, ly);
        float dist = length(vUv - vec2(0.5));
        float fade = 1.0 - smoothstep(0.3, 0.5, dist);
        gl_FragColor = vec4(0.0, 0.96, 1.0, grid * fade * 0.12);
      }
    `,
    transparent: true,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const grid = new THREE.Mesh(gridGeo, gridMat);
  grid.rotation.x = -Math.PI / 2.5;
  grid.position.y = -8;
  scene.add(grid);

  /* ── mouse parallax ── */
  let targetX = 0, targetY = 0, currentX = 0, currentY = 0;
  document.addEventListener('mousemove', (e) => {
    targetX = (e.clientX / window.innerWidth - 0.5) * 2;
    targetY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  /* ── resize ── */
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  /* ── animate ── */
  let time = 0;
  (function animate() {
    requestAnimationFrame(animate);
    time += 0.008;

    starMat.uniforms.time.value = time;
    pMat.uniforms.time.value    = time;
    gridMat.uniforms.time.value = time;

    /* update particle positions */
    const pos = pGeo.attributes.position.array;
    for (let i = 0; i < particleCount; i++) {
      pos[i * 3]     += pVel[i * 3];
      pos[i * 3 + 1] += pVel[i * 3 + 1];
      /* wrap */
      if (pos[i * 3 + 1] > 22) {
        pos[i * 3 + 1] = -22;
        pos[i * 3]     = rand(-30, 30);
      }
    }
    pGeo.attributes.position.needsUpdate = true;

    /* camera drift */
    currentX = lerp(currentX, targetX * 0.4, 0.04);
    currentY = lerp(currentY, targetY * 0.3, 0.04);
    camera.position.x = currentX;
    camera.position.y = currentY * 0.5 + Math.sin(time * 0.2) * 0.3;
    camera.rotation.z = currentX * 0.04;

    /* slow rotate particles */
    particles.rotation.y = time * 0.05;

    renderer.render(scene, camera);
  })();
}

/* ════════════════════════════════════
   HOLOGRAM CORE (canvas 2D)
   ════════════════════════════════════ */
function initHoloCanvas() {
  const canvas = $('#holo-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  let t = 0;
  (function draw() {
    requestAnimationFrame(draw);
    const { width: W, height: H } = canvas;
    ctx.clearRect(0, 0, W, H);
    t += 0.02;

    const cx = W / 2, cy = H / 2;
    const r  = Math.min(W, H) / 2 - 8;

    /* rotating rings */
    for (let ring = 0; ring < 3; ring++) {
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(t * (ring % 2 === 0 ? 1 : -1) * (0.5 + ring * 0.3));
      ctx.strokeStyle = `hsla(${185 + ring * 60}, 100%, 65%, ${0.3 - ring * 0.06})`;
      ctx.lineWidth   = 1;
      ctx.setLineDash([4, 8]);
      ctx.beginPath();
      ctx.arc(0, 0, r - ring * 14, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }

    /* data pulse arcs */
    for (let a = 0; a < 5; a++) {
      const angle = (t * 0.7 + a * (Math.PI * 2 / 5));
      const px = cx + Math.cos(angle) * r * 0.55;
      const py = cy + Math.sin(angle) * r * 0.55;
      const grad = ctx.createRadialGradient(px, py, 0, px, py, 14);
      grad.addColorStop(0, `hsla(${185 + a * 30}, 100%, 70%, 0.9)`);
      grad.addColorStop(1, 'transparent');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    /* centre glow */
    const cg = ctx.createRadialGradient(cx, cy, 0, cx, cy, r * 0.35);
    cg.addColorStop(0, 'rgba(0,245,255,0.25)');
    cg.addColorStop(1, 'transparent');
    ctx.fillStyle = cg;
    ctx.beginPath();
    ctx.arc(cx, cy, r * 0.35, 0, Math.PI * 2);
    ctx.fill();

    /* scanline sweep */
    const sy = (Math.sin(t) * 0.5 + 0.5) * H;
    const sg = ctx.createLinearGradient(0, sy - 20, 0, sy + 20);
    sg.addColorStop(0, 'transparent');
    sg.addColorStop(0.5, 'rgba(0,245,255,0.15)');
    sg.addColorStop(1, 'transparent');
    ctx.fillStyle = sg;
    ctx.fillRect(0, sy - 20, W, 40);
  })();
}

/* ════════════════════════════════════
   NETWORK CANVAS (2D)
   ════════════════════════════════════ */
function initNetworkCanvas() {
  const canvas = $('#network-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const wrap = canvas.parentElement;

  function resize() {
    canvas.width  = wrap.offsetWidth;
    canvas.height = wrap.offsetHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const nodeCount = 28;
  const nodes = Array.from({ length: nodeCount }, () => ({
    x: rand(0.05, 0.95),
    y: rand(0.05, 0.95),
    vx: rand(-0.0006, 0.0006),
    vy: rand(-0.0006, 0.0006),
    r: rand(3, 7),
    color: ['#00f5ff','#a855f7','#10b981','#f59e0b'][Math.floor(Math.random()*4)],
    pulse: rand(0, Math.PI * 2),
  }));

  const pulses = [];
  function spawnPulse() {
    const n = nodes[Math.floor(Math.random() * nodeCount)];
    pulses.push({ x: n.x, y: n.y, r: 0, maxR: 0.06, alpha: 1, color: n.color });
  }
  setInterval(spawnPulse, 800);

  let t = 0;
  (function draw() {
    requestAnimationFrame(draw);
    t += 0.01;
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    /* background grid */
    ctx.strokeStyle = 'rgba(0,245,255,0.04)';
    ctx.lineWidth = 0.5;
    for (let x = 0; x < W; x += 40) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y < H; y += 40) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }

    /* update + draw nodes */
    nodes.forEach(n => {
      n.x += n.vx; n.y += n.vy;
      if (n.x < 0.02 || n.x > 0.98) n.vx *= -1;
      if (n.y < 0.02 || n.y > 0.98) n.vy *= -1;
      n.pulse += 0.05;
    });

    /* edges */
    for (let i = 0; i < nodeCount; i++) {
      for (let j = i + 1; j < nodeCount; j++) {
        const a = nodes[i], b = nodes[j];
        const dx = (a.x - b.x) * W, dy = (a.y - b.y) * H;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 140) {
          const alpha = (1 - dist / 140) * 0.35;
          const grad = ctx.createLinearGradient(a.x*W, a.y*H, b.x*W, b.y*H);
          grad.addColorStop(0, a.color + Math.floor(alpha * 255).toString(16).padStart(2,'0'));
          grad.addColorStop(1, b.color + Math.floor(alpha * 255).toString(16).padStart(2,'0'));
          ctx.strokeStyle = grad;
          ctx.lineWidth = alpha * 2;
          ctx.beginPath();
          ctx.moveTo(a.x * W, a.y * H);
          ctx.lineTo(b.x * W, b.y * H);
          ctx.stroke();

          /* data packet */
          const prog = ((t * 0.4 + i * 0.1) % 1);
          const px = a.x + (b.x - a.x) * prog;
          const py = a.y + (b.y - a.y) * prog;
          ctx.fillStyle = a.color;
          ctx.shadowColor = a.color;
          ctx.shadowBlur = 6;
          ctx.beginPath();
          ctx.arc(px * W, py * H, 2, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      }
    }

    /* draw node circles */
    nodes.forEach(n => {
      const glow = Math.sin(n.pulse) * 0.5 + 0.5;
      ctx.shadowColor = n.color;
      ctx.shadowBlur  = 12 + glow * 12;
      ctx.fillStyle   = n.color;
      ctx.beginPath();
      ctx.arc(n.x * W, n.y * H, n.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    /* pulse rings */
    for (let i = pulses.length - 1; i >= 0; i--) {
      const p = pulses[i];
      p.r += 0.003; p.alpha -= 0.02;
      if (p.alpha <= 0) { pulses.splice(i, 1); continue; }
      ctx.strokeStyle = p.color;
      ctx.globalAlpha = p.alpha * 0.5;
      ctx.lineWidth   = 1;
      ctx.beginPath();
      ctx.arc(p.x * W, p.y * H, p.r * Math.min(W, H), 0, Math.PI * 2);
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
  })();
}

/* ════════════════════════════════════
   LIVE DATA FEED
   ════════════════════════════════════ */
function initLiveFeed() {
  const container = $('#feed-entries');
  if (!container) return;
  const events = [
    ['NODE', 'Node 0x4A2F connected from sector 3-Delta'],
    ['DATA', 'Quantum packet 98.2KB transferred — latency 0.0001ms'],
    ['SEC',  'Auth challenge resolved — key entropy: 4096-bit'],
    ['SYNC', 'Neural bridge sync: 99.97% coherence achieved'],
    ['WARN', 'Anomaly detected in sector 12 — auto-resolved'],
    ['NET',  'Mesh density increased to 847K nodes'],
    ['SYS',  'Quantum core temperature: 0.004K — optimal'],
    ['DATA', 'Cross-dimensional packet relay initiated'],
    ['NODE', 'Node cluster 7-Alpha reporting full sync'],
    ['SEC',  'Intrusion attempt blocked — origin: unknown'],
  ];
  let idx = 0;
  function addEntry() {
    const [type, msg] = events[idx % events.length]; idx++;
    const now = new Date();
    const time = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`;
    const el = document.createElement('div');
    el.className = 'feed-entry';
    el.innerHTML = `<span class="fe-time">${time}</span><span class="fe-type">[${type}]</span>${msg}`;
    container.prepend(el);
    const children = container.children;
    if (children.length > 6) children[children.length - 1].remove();
  }
  addEntry();
  setInterval(addEntry, 1800);
}

/* ════════════════════════════════════
   TILT CARDS
   ════════════════════════════════════ */
function initTiltCards() {
  $$('[data-tilt]').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width  - 0.5;
      const y = (e.clientY - rect.top)  / rect.height - 0.5;
      card.style.transform = `perspective(800px) rotateY(${x * 12}deg) rotateX(${-y * 10}deg) translateY(-6px)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });
}

/* ════════════════════════════════════
   INTERSECTION OBSERVER — reveal
   ════════════════════════════════════ */
function initReveal() {
  /* add reveal class to targets */
  $$('.holo-card, .tl-card, .section-header, .info-panel, .live-feed, .bandwidth-monitor').forEach(el => {
    el.classList.add('reveal');
  });

  /* timeline items */
  $$('.timeline-item').forEach((el, i) => {
    el.style.transitionDelay = i * 0.15 + 's';
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });

  $$('.reveal, .timeline-item').forEach(el => observer.observe(el));
}

/* ════════════════════════════════════
   STAT COUNTER
   ════════════════════════════════════ */
function initCounters() {
  const nums = $$('.stat-num[data-target]');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      const el  = e.target;
      const end = parseFloat(el.dataset.target);
      const dec = (end % 1 !== 0) ? 1 : 0;
      let start = 0, dur = 1600, step = 16;
      const inc = end / (dur / step);
      const timer = setInterval(() => {
        start = Math.min(start + inc, end);
        el.textContent = start.toFixed(dec);
        if (start >= end) clearInterval(timer);
      }, step);
      observer.unobserve(el);
    });
  }, { threshold: 0.5 });
  nums.forEach(n => observer.observe(n));
}

/* ════════════════════════════════════
   NAV SCROLL EFFECT
   ════════════════════════════════════ */
function initNav() {
  const nav   = $('#main-nav');
  const links = $$('.nav-link');
  const sections = $$('.section');

  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 60);

    /* active link */
    let current = '';
    sections.forEach(sec => {
      if (window.scrollY >= sec.offsetTop - 120) current = '#' + sec.id;
    });
    links.forEach(l => {
      l.classList.toggle('active', l.getAttribute('href') === current);
    });
  });

  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = $(link.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    });
  });
}

/* ════════════════════════════════════
   ENTER BUTTON PARTICLES
   ════════════════════════════════════ */
function initEnterButton() {
  const btn = $('#enter-btn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const systems = $('#systems');
    if (systems) systems.scrollIntoView({ behavior: 'smooth' });
    /* burst effect */
    for (let i = 0; i < 12; i++) {
      const p = document.createElement('div');
      p.style.cssText = `
        position:fixed; z-index:9999; pointer-events:none;
        width:4px; height:4px; border-radius:50%;
        background:${['#00f5ff','#a855f7','#ff006e'][Math.floor(Math.random()*3)]};
        left:${btn.getBoundingClientRect().left + btn.offsetWidth/2}px;
        top:${btn.getBoundingClientRect().top + btn.offsetHeight/2}px;
        transform:translate(-50%,-50%);
        box-shadow: 0 0 8px currentColor;
      `;
      document.body.appendChild(p);
      const angle = (i / 12) * Math.PI * 2;
      const dist  = rand(40, 100);
      let prog = 0;
      const bx = Math.cos(angle) * dist, by = Math.sin(angle) * dist;
      (function anim() {
        if (prog >= 1) { p.remove(); return; }
        prog += 0.04;
        p.style.transform = `translate(calc(-50% + ${bx * prog}px), calc(-50% + ${by * prog}px))`;
        p.style.opacity   = 1 - prog;
        requestAnimationFrame(anim);
      })();
    }
  });
}

/* ════════════════════════════════════
   TERMINAL INPUT
   ════════════════════════════════════ */
function initTerminal() {
  const btn   = $('#connect-btn');
  const input = $('#email-input');
  if (!btn || !input) return;

  btn.addEventListener('click', () => {
    const val = input.value.trim();
    if (!val) {
      input.placeholder = 'COORDINATES REQUIRED //';
      setTimeout(() => (input.placeholder = 'enter.your@coordinates.io'), 2000);
      return;
    }
    input.value = '';
    input.placeholder = 'CONNECTION ESTABLISHED — WELCOME TO THE NEXUS';
    btn.innerHTML = '<span>CONNECTED ✓</span><div class="terminal-btn-glow"></div>';
    btn.style.background = '#10b981';
    setTimeout(() => {
      input.placeholder = 'enter.your@coordinates.io';
      btn.innerHTML = '<span>CONNECT</span><div class="terminal-btn-glow"></div>';
      btn.style.background = '';
    }, 3000);
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') btn.click();
  });
}

/* ════════════════════════════════════
   START ALL
   ════════════════════════════════════ */
function startAnimations() {
  initParticleBackground();
  initHoloCanvas();
  initNetworkCanvas();
  initLiveFeed();
  initTiltCards();
  initReveal();
  initCounters();
  initNav();
  initEnterButton();
  initTerminal();
}

/* ── boot ── */
document.addEventListener('DOMContentLoaded', () => {
  initCursor();
  initLoader();
});
