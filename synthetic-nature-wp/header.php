<!doctype html>
<html <?php language_attributes(); ?>>
<head>
  <meta charset="<?php bloginfo('charset'); ?>">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div class="sn-wrapper">

  <!-- VIDEO BACKGROUND -->
  <?php $video_url = sn_get('sn_video_url', 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260619_191346_9d19d66e-86a4-47f7-8dc6-712c1788c3b2.mp4'); ?>
  <?php if ($video_url): ?>
  <div class="sn-video-bg" aria-hidden="true">
    <video autoplay muted loop playsinline>
      <source src="<?php echo esc_url($video_url); ?>" type="video/mp4">
    </video>
  </div>
  <?php endif; ?>

  <!-- NAVIGATION -->
  <nav class="sn-nav" role="navigation" aria-label="<?php esc_attr_e('Primary', 'synthetic-nature'); ?>">

    <!-- Brand -->
    <a href="<?php echo esc_url(home_url('/')); ?>" class="sn-brand">
      <?php echo esc_html(sn_get('sn_brand_name', get_bloginfo('name'))); ?>
    </a>

    <!-- Desktop menu -->
    <?php
    wp_nav_menu([
      'theme_location' => 'primary',
      'menu_class'     => 'sn-nav-links',
      'container'      => false,
      'fallback_cb'    => 'sn_fallback_nav',
      'depth'          => 1,
    ]);
    ?>

    <!-- Hamburger -->
    <button
      id="sn-hamburger"
      class="sn-hamburger"
      aria-controls="sn-mobile-menu"
      aria-expanded="false"
      aria-label="<?php esc_attr_e('Open menu', 'synthetic-nature'); ?>"
    >
      <!-- Menu icon -->
      <svg id="sn-icon-menu" viewBox="0 0 24 24" aria-hidden="true">
        <line x1="3" y1="6"  x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
      <!-- Close icon -->
      <svg id="sn-icon-close" viewBox="0 0 24 24" aria-hidden="true" style="display:none">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6"  y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  </nav>

  <!-- MOBILE MENU -->
  <div id="sn-mobile-menu" class="sn-mobile-menu" role="dialog" aria-label="<?php esc_attr_e('Mobile navigation', 'synthetic-nature'); ?>">
    <?php
    wp_nav_menu([
      'theme_location' => 'primary',
      'container'      => false,
      'menu_class'     => '',
      'fallback_cb'    => 'sn_fallback_nav',
      'depth'          => 1,
    ]);
    ?>
  </div>
