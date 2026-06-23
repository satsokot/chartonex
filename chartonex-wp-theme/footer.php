<!-- ══ FOOTER ══ -->
<footer class="cx-footer" role="contentinfo">
  <div class="cx-footer-inner">
    <div class="cx-footer-top">

      <!-- Brand -->
      <div class="cx-footer-brand">
        <a href="<?php echo esc_url(home_url('/')); ?>" class="cx-logo" aria-label="Chartonex">
          <svg width="32" height="32" viewBox="0 0 48 48" fill="none">
            <defs>
              <linearGradient id="footerLogoGrad" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                <stop stop-color="#A855F7"/><stop offset="1" stop-color="#22D3EE"/>
              </linearGradient>
              <linearGradient id="footerLogoBg" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                <stop stop-color="#7C3AED" stop-opacity="0.2"/><stop offset="1" stop-color="#06B6D4" stop-opacity="0.2"/>
              </linearGradient>
            </defs>
            <rect width="48" height="48" rx="12" fill="url(#footerLogoBg)"/>
            <rect width="48" height="48" rx="12" stroke="url(#footerLogoGrad)" stroke-width="1" fill="none"/>
            <path d="M28 10 C18 10, 10 17, 10 24 C10 31, 18 38, 28 38" stroke="url(#footerLogoGrad)" stroke-width="3.5" stroke-linecap="round" fill="none"/>
            <path d="M30 14 L42 34" stroke="url(#footerLogoGrad)" stroke-width="3.5" stroke-linecap="round"/>
            <path d="M30 34 L42 14" stroke="url(#footerLogoGrad)" stroke-width="3.5" stroke-linecap="round"/>
          </svg>
          <div>
            <div class="cx-logo-name">Chartonex</div>
            <div class="cx-logo-tagline">Beyond Charts</div>
          </div>
        </a>
        <p style="margin-top:16px;">
          10+ years of crypto expertise, rebuilt as a modern AI-powered trading intelligence platform for crypto, gold, and forex markets.
        </p>
      </div>

      <!-- Platform links -->
      <div class="cx-footer-col">
        <h4>Platform</h4>
        <ul>
          <li><a href="#features">Features</a></li>
          <li><a href="#markets">Markets</a></li>
          <li><a href="#how-it-works">How It Works</a></li>
          <li><a href="#cta">Early Access</a></li>
        </ul>
      </div>

      <!-- Markets -->
      <div class="cx-footer-col">
        <h4>Markets</h4>
        <ul>
          <li><a href="#markets">Cryptocurrency</a></li>
          <li><a href="#markets">Gold &amp; Metals</a></li>
          <li><a href="#markets">Forex</a></li>
          <li><a href="#markets">DEX Trading</a></li>
        </ul>
      </div>

      <!-- Company -->
      <div class="cx-footer-col">
        <h4>Company</h4>
        <ul>
          <li><a href="<?php echo esc_url(home_url('/about')); ?>">About</a></li>
          <li><a href="<?php echo esc_url(home_url('/blog')); ?>">Blog</a></li>
          <li><a href="<?php echo esc_url(home_url('/contact')); ?>">Contact</a></li>
          <li><a href="<?php echo esc_url(home_url('/privacy')); ?>">Privacy Policy</a></li>
        </ul>
      </div>
    </div>

    <div class="cx-footer-bottom">
      <p>&copy; <?php echo date('Y'); ?> Chartonex. All rights reserved. Built for traders, by traders.</p>
      <div class="cx-footer-socials">
        <a href="#" class="cx-social-btn" aria-label="Telegram">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.248l-2.01 9.461c-.148.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.873.76z"/></svg>
        </a>
        <a href="#" class="cx-social-btn" aria-label="Twitter / X">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        </a>
        <a href="#" class="cx-social-btn" aria-label="Instagram">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>
        </a>
      </div>
    </div>
  </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
