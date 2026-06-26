<?php
/**
 * Chartonex — index.php
 * Front page falls through to the landing template.
 */

if (is_front_page()) {
    get_header();
    include get_template_directory() . '/templates/landing-content.php';
    get_footer();
} else {
    // Fallback for inner pages
    get_header();
    ?>
    <main style="max-width:860px;margin:120px auto;padding:0 24px;">
      <?php if (have_posts()) : while (have_posts()) : the_post(); ?>
        <h1 style="font-family:'Space Grotesk',sans-serif;font-size:clamp(28px,4vw,48px);font-weight:700;margin-bottom:24px;">
          <?php the_title(); ?>
        </h1>
        <div style="color:var(--text-secondary);font-size:17px;line-height:1.8;">
          <?php the_content(); ?>
        </div>
      <?php endwhile; endif; ?>
    </main>
    <?php
    get_footer();
}
