<?php get_header(); ?>

  <main class="sn-hero" id="main-content">

    <h1 class="sn-title">
      <span class="line" data-text="<?php echo esc_attr(sn_get('sn_title_line1', 'WITNESS THE')); ?>"></span>
      <span class="line" data-text="<?php echo esc_attr(sn_get('sn_title_line2', 'HIDDEN REALM')); ?>"></span>
    </h1>

    <p class="sn-subtitle">
      <?php echo wp_kses_post(sn_get('sn_subtitle', 'An odyssey through delicate living forms, revealed by lens and curiosity.')); ?>
    </p>

    <a href="<?php echo esc_url(sn_get('sn_cta_url', '#')); ?>" class="sn-cta">
      <?php echo esc_html(sn_get('sn_cta_text', 'Begin the Experience')); ?>
    </a>

  </main>

<?php get_footer(); ?>
