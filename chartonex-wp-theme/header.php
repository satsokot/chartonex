<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
  <meta charset="<?php bloginfo('charset'); ?>">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="<?php bloginfo('description'); ?>">
  <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<!-- ══ NAVBAR ══ -->
<nav class="cx-nav" id="cx-nav" role="navigation" aria-label="Main navigation">
  <div class="cx-nav-inner">

    <!-- Logo -->
    <a href="<?php echo esc_url(home_url('/')); ?>" class="cx-logo" aria-label="Chartonex Home">
      <svg class="cx-logo-svg" width="36" height="36" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="navLogoGrad" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
            <stop stop-color="#A855F7"/>
            <stop offset="1" stop-color="#22D3EE"/>
          </linearGradient>
          <linearGradient id="navLogoBg" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
            <stop stop-color="#7C3AED" stop-opacity="0.25"/>
            <stop offset="1" stop-color="#06B6D4" stop-opacity="0.25"/>
          </linearGradient>
        </defs>
        <rect width="48" height="48" rx="12" fill="url(#navLogoBg)"/>
        <rect width="48" height="48" rx="12" stroke="url(#navLogoGrad)" stroke-width="1" fill="none"/>
        <path d="M28 10 C18 10, 10 17, 10 24 C10 31, 18 38, 28 38" stroke="url(#navLogoGrad)" stroke-width="3.5" stroke-linecap="round" fill="none"/>
        <path d="M30 14 L42 34" stroke="url(#navLogoGrad)" stroke-width="3.5" stroke-linecap="round"/>
        <path d="M30 34 L42 14" stroke="url(#navLogoGrad)" stroke-width="3.5" stroke-linecap="round"/>
        <circle cx="30" cy="34" r="2" fill="#22D3EE" opacity="0.8"/>
        <circle cx="36" cy="24" r="2" fill="#A855F7" opacity="0.8"/>
        <circle cx="42" cy="14" r="2" fill="#22D3EE" opacity="0.8"/>
      </svg>
      <div>
        <div class="cx-logo-name">Chartonex</div>
        <div class="cx-logo-tagline">Beyond Charts</div>
      </div>
    </a>

    <!-- Desktop links -->
    <div class="cx-nav-links">
      <a href="#features"    class="cx-nav-link">Features</a>
      <a href="#how-it-works"class="cx-nav-link">How It Works</a>
      <a href="#markets"     class="cx-nav-link">Markets</a>
      <a href="#stats"       class="cx-nav-link">Stats</a>
    </div>

    <!-- CTA -->
    <div class="cx-nav-cta">
      <a href="#cta" class="cx-btn-primary">
        Get Early Access
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </a>
      <button class="cx-hamburger" aria-label="Menu" aria-expanded="false">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
    </div>
  </div>

  <!-- Mobile menu -->
  <div class="cx-mobile-menu" style="display:none;">
    <a href="#features">Features</a>
    <a href="#how-it-works">How It Works</a>
    <a href="#markets">Markets</a>
    <a href="#stats">Stats</a>
    <a href="#cta" class="cx-btn-primary" style="margin:12px 24px;display:inline-flex;width:auto;">Get Early Access</a>
  </div>
</nav>
