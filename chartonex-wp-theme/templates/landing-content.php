<?php defined('ABSPATH') || exit; ?>

<!-- ══════════════════════════════════════
     CHARTONEX LANDING PAGE — Full Content
     ══════════════════════════════════════ -->

<!-- ── HERO ── -->
<section class="cx-hero" id="hero">
  <div class="cx-hero-bg"></div>
  <div class="cx-hero-grid"></div>

  <div class="cx-hero-inner">
    <!-- Left -->
    <div class="cx-hero-content">
      <div class="cx-hero-badge">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#A855F7" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        Next-Gen Trading Intelligence
      </div>

      <h1 class="cx-hero-title">
        Trade Smarter.&nbsp;
        <span class="cx-gradient-text">Go Beyond</span><br>
        the Charts.
      </h1>

      <p class="cx-hero-desc">
        Chartonex combines advanced market analysis, AI-driven signals, and real-time intelligence for crypto, gold, and forex — all in one unified platform.
      </p>

      <div class="cx-hero-actions">
        <a href="#cta" class="cx-btn-primary">
          Start Trading Now
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </a>
        <a href="#features" class="cx-btn-outline">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>
          Watch Demo
        </a>
      </div>

      <div class="cx-hero-trust">
        <div class="cx-hero-trust-item">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.5"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
          10+ Years Experience
        </div>
        <div class="cx-hero-trust-item">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Secure & Transparent
        </div>
        <div class="cx-hero-trust-item">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          Real-time Signals
        </div>
      </div>
    </div>

    <!-- Right: Chart panel -->
    <div style="position:relative;">
      <div class="cx-chart-panel cx-glow-border">
        <!-- Top bar -->
        <div class="cx-chart-topbar">
          <div>
            <div class="cx-chart-pair">BTC/USDT</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">Binance · 1H</div>
          </div>
          <div style="text-align:right;">
            <div class="cx-chart-price">$68,420</div>
            <div class="cx-chart-change" style="margin-top:4px;">+2.34%</div>
          </div>
        </div>

        <!-- SVG chart -->
        <div class="cx-chart-canvas-wrap">
          <svg class="cx-chart-svg" viewBox="0 0 500 180" preserveAspectRatio="none">
            <!-- Built dynamically by JS -->
          </svg>
        </div>

        <!-- Ticker cards -->
        <div class="cx-chart-tickers">
          <div class="cx-ticker-card">
            <div class="cx-ticker-sym">BTC/USDT</div>
            <div class="cx-ticker-val">$68,420</div>
            <div class="cx-ticker-chg up">+2.34%</div>
          </div>
          <div class="cx-ticker-card">
            <div class="cx-ticker-sym">ETH/USDT</div>
            <div class="cx-ticker-val">$3,847</div>
            <div class="cx-ticker-chg up">+1.87%</div>
          </div>
          <div class="cx-ticker-card">
            <div class="cx-ticker-sym">XAU/USD</div>
            <div class="cx-ticker-val">$2,318</div>
            <div class="cx-ticker-chg down">-0.42%</div>
          </div>
        </div>
      </div>

      <!-- Floating signal card -->
      <div class="cx-signal-float">
        <div class="cx-signal-label">AI Signal</div>
        <div class="cx-signal-value">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/></svg>
          STRONG BUY
        </div>
      </div>

      <!-- Floating volume card -->
      <div class="cx-volume-float">
        <div class="cx-signal-label">24h Vol</div>
        <div style="font-size:14px;font-weight:700;color:#22D3EE;margin-top:2px;">$4.2B</div>
      </div>
    </div>
  </div>
</section>

<!-- ── STATS STRIP ── -->
<section class="cx-stats" id="stats">
  <div class="cx-stats-inner">
    <div class="cx-stat-card cx-animate-observe">
      <div class="cx-stat-num" data-target="10" data-suffix="+" >10+</div>
      <div class="cx-stat-label">Years of Market Experience</div>
    </div>
    <div class="cx-stat-card cx-animate-observe cx-delay-1">
      <div class="cx-stat-num" data-target="50000" data-suffix="+">50K+</div>
      <div class="cx-stat-label">Active Traders</div>
    </div>
    <div class="cx-stat-card cx-animate-observe cx-delay-2">
      <div class="cx-stat-num" data-target="99.9" data-suffix="%" data-decimals="1">99.9%</div>
      <div class="cx-stat-label">Platform Uptime</div>
    </div>
    <div class="cx-stat-card cx-animate-observe cx-delay-3">
      <div class="cx-stat-num" data-target="3" data-suffix=" Markets">3</div>
      <div class="cx-stat-label">Crypto · Gold · Forex</div>
    </div>
  </div>
</section>

<!-- ── FEATURES ── -->
<section class="cx-section cx-features" id="features">
  <div class="cx-container">
    <div class="cx-features-header cx-animate-observe">
      <div class="cx-section-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        Platform Features
      </div>
      <h2 class="cx-section-title">Everything You Need to Trade <span class="cx-gradient-text">Intelligently</span></h2>
      <p class="cx-section-sub">From AI-powered signals to real-time market radar — Chartonex gives you the edge the market doesn't want you to have.</p>
    </div>

    <div class="cx-features-grid">
      <?php
      $features = [
        ['🤖', 'AI Signal Engine',     'Machine learning models scan thousands of data points per second — delivering high-confidence trade setups before they become obvious.',     'NEW'],
        ['📡', 'News Radar',           'Real-time news analysis with sentiment scoring. Know how macro events move crypto, gold, and forex markets — before the herd reacts.',     'LIVE'],
        ['🧠', 'Smart Money Tracker',  'Follow institutional flows via COT data, ETF movements, and on-chain whale activity. Trade with the big players, not against them.',       'PRO'],
        ['⚡', 'DEX Bot',             'Semi-automated memecoin detection with 5-layer safety checks. Human-in-the-loop design keeps you in control of every position.',            'BETA'],
        ['📊', 'Multi-Market Dashboard','One unified view for crypto, gold, and forex. Switch markets in a click. Never miss an opportunity across asset classes.',              ''],
        ['🔒', 'Privacy-First',        'We profit when you profit — not from your mistakes. Your data stays yours. No data selling, no hidden incentives, no manipulation.',    ''],
      ];
      foreach ($features as $i => [$icon, $title, $desc, $tag]) :
        $delay = $i < 3 ? "cx-delay-{$i}" : "cx-delay-" . ($i - 3);
      ?>
      <div class="cx-feature-card cx-animate-observe <?= esc_attr($delay) ?>">
        <div class="cx-feature-icon"><?= $icon ?></div>
        <h3 class="cx-feature-title"><?= esc_html($title) ?></h3>
        <p class="cx-feature-desc"><?= esc_html($desc) ?></p>
        <?php if ($tag) : ?>
        <span class="cx-feature-tag"><?= esc_html($tag) ?></span>
        <?php endif; ?>
      </div>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<!-- ── HOW IT WORKS ── -->
<section class="cx-section cx-how" id="how-it-works">
  <div class="cx-container">
    <div class="cx-how-header cx-animate-observe">
      <div class="cx-section-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        Simple Process
      </div>
      <h2 class="cx-section-title">From Signal to <span class="cx-gradient-text">Profit</span> in 3 Steps</h2>
      <p class="cx-section-sub">Chartonex is designed for traders who want results, not complexity. The system works — you just supervise.</p>
    </div>

    <div class="cx-how-steps">
      <?php
      $steps = [
        ['Connect Your Markets',   'Link your exchange accounts and select the assets you trade — crypto, gold, or forex. Chartonex aggregates all data into one live view.'],
        ['Receive AI-Powered Signals', 'Our multi-layer engine analyzes news sentiment, on-chain data, order flow, and technical patterns. You get clean, actionable signals with context.'],
        ['Execute & Grow',         'Review signals, approve trades with one tap, and let the system manage position tracking. Human-in-the-loop — always in control.'],
      ];
      foreach ($steps as $i => [$title, $desc]) :
      ?>
      <div class="cx-step cx-animate-observe cx-delay-<?= $i ?>">
        <div class="cx-step-num"><?= $i + 1 ?></div>
        <div class="cx-step-content">
          <h3 class="cx-step-title"><?= esc_html($title) ?></h3>
          <p class="cx-step-desc"><?= esc_html($desc) ?></p>
        </div>
      </div>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<!-- ── MARKETS ── -->
<section class="cx-section" id="markets">
  <div class="cx-container">
    <div class="cx-center cx-animate-observe" style="margin-bottom:64px;">
      <div class="cx-section-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
        Supported Markets
      </div>
      <h2 class="cx-section-title">Trade What <span class="cx-gradient-text">Moves the World</span></h2>
      <p class="cx-section-sub cx-center">Three of the most liquid asset classes — all covered under one intelligent roof.</p>
    </div>

    <div class="cx-markets-grid">
      <div class="cx-market-card crypto cx-animate-observe">
        <div class="cx-market-icon">₿</div>
        <h3 class="cx-market-name">Cryptocurrency</h3>
        <p class="cx-market-desc">Spot, futures, and DEX trading. From blue-chip BTC/ETH to high-potential memecoins — with on-chain intelligence built in.</p>
        <div class="cx-market-tags">
          <span class="cx-market-tag">BTC</span>
          <span class="cx-market-tag">ETH</span>
          <span class="cx-market-tag">Altcoins</span>
          <span class="cx-market-tag">DEX</span>
        </div>
      </div>

      <div class="cx-market-card gold cx-animate-observe cx-delay-1">
        <div class="cx-market-icon">🥇</div>
        <h3 class="cx-market-name">Gold & Metals</h3>
        <p class="cx-market-desc">Real-time XAU/USD analysis backed by global central bank flows, World Gold Council data, and macro sentiment scoring.</p>
        <div class="cx-market-tags">
          <span class="cx-market-tag">XAU/USD</span>
          <span class="cx-market-tag">XAG/USD</span>
          <span class="cx-market-tag">Futures</span>
        </div>
      </div>

      <div class="cx-market-card forex cx-animate-observe cx-delay-2">
        <div class="cx-market-icon">💱</div>
        <h3 class="cx-market-name">Forex</h3>
        <p class="cx-market-desc">Major, minor, and exotic pairs. Powered by CFTC COT data, central bank event tracking, and real-time economic calendar.</p>
        <div class="cx-market-tags">
          <span class="cx-market-tag">EUR/USD</span>
          <span class="cx-market-tag">GBP/USD</span>
          <span class="cx-market-tag">Majors</span>
          <span class="cx-market-tag">Exotics</span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ── CTA ── -->
<section class="cx-cta" id="cta">
  <div class="cx-container">
    <div class="cx-cta-inner cx-animate-observe">
      <div class="cx-cta-glow-l"></div>
      <div class="cx-cta-glow-r"></div>

      <div class="cx-section-label" style="margin:0 auto 24px;display:inline-flex;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        Limited Early Access
      </div>

      <h2 class="cx-cta-title">
        Ready to Trade <span class="cx-gradient-text">Beyond Charts?</span>
      </h2>
      <p class="cx-cta-desc">
        Join thousands of traders who already use Chartonex intelligence to navigate crypto, gold, and forex with clarity and confidence.
      </p>

      <div class="cx-cta-actions">
        <a href="<?php echo esc_url(home_url('/register')); ?>" class="cx-btn-primary">
          Start Free Today
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </a>
        <a href="<?php echo esc_url(home_url('/contact')); ?>" class="cx-btn-outline">
          Talk to Sales
        </a>
      </div>
    </div>
  </div>
</section>
