<?php
defined('ABSPATH') || exit;

/* ══════════════════════════════
   Enqueue styles & scripts
══════════════════════════════ */
function sn_enqueue_assets() {
    wp_enqueue_style(
        'sn-fonts',
        'https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500&display=swap',
        [], null
    );
    wp_enqueue_style(
        'sn-garamond',
        'https://db.onlinewebfonts.com/c/2bf40ab72ea4897a3fd9b6e48b233a19?family=Garamond',
        [], null
    );
    wp_enqueue_style(
        'sn-main',
        get_template_directory_uri() . '/assets/css/main.css',
        ['sn-fonts', 'sn-garamond'],
        '1.0'
    );
    wp_enqueue_script(
        'sn-main',
        get_template_directory_uri() . '/assets/js/main.js',
        [], '1.0', true
    );
}
add_action('wp_enqueue_scripts', 'sn_enqueue_assets');

/* ══════════════════════════════
   Register nav menus
══════════════════════════════ */
function sn_register_menus() {
    register_nav_menus([
        'primary' => __('Primary Navigation', 'synthetic-nature'),
    ]);
}
add_action('after_setup_theme', 'sn_register_menus');

/* ══════════════════════════════
   Theme support
══════════════════════════════ */
function sn_theme_support() {
    add_theme_support('title-tag');
    add_theme_support('custom-logo');
    add_theme_support('html5', ['search-form', 'gallery', 'caption']);
}
add_action('after_setup_theme', 'sn_theme_support');

/* ══════════════════════════════
   Customizer settings
══════════════════════════════ */
function sn_customizer(WP_Customize_Manager $wp_customize) {

    // ── Panel ──────────────────────────────────────
    $wp_customize->add_panel('sn_panel', [
        'title'    => __('Synthetic Nature Hero', 'synthetic-nature'),
        'priority' => 30,
    ]);

    // ── Section: Brand ──────────────────────────────
    $wp_customize->add_section('sn_brand', [
        'title' => __('Brand Name', 'synthetic-nature'),
        'panel' => 'sn_panel',
    ]);
    $wp_customize->add_setting('sn_brand_name', [
        'default'           => 'Organic Visions',
        'sanitize_callback' => 'sanitize_text_field',
        'transport'         => 'postMessage',
    ]);
    $wp_customize->add_control('sn_brand_name', [
        'label'   => __('Brand / Site Name', 'synthetic-nature'),
        'section' => 'sn_brand',
        'type'    => 'text',
    ]);

    // ── Section: Hero ───────────────────────────────
    $wp_customize->add_section('sn_hero', [
        'title' => __('Hero Text', 'synthetic-nature'),
        'panel' => 'sn_panel',
    ]);

    // Title line 1
    $wp_customize->add_setting('sn_title_line1', [
        'default'           => 'WITNESS THE',
        'sanitize_callback' => 'sanitize_text_field',
        'transport'         => 'postMessage',
    ]);
    $wp_customize->add_control('sn_title_line1', [
        'label'   => __('Heading Line 1', 'synthetic-nature'),
        'section' => 'sn_hero',
        'type'    => 'text',
    ]);

    // Title line 2
    $wp_customize->add_setting('sn_title_line2', [
        'default'           => 'HIDDEN REALM',
        'sanitize_callback' => 'sanitize_text_field',
        'transport'         => 'postMessage',
    ]);
    $wp_customize->add_control('sn_title_line2', [
        'label'   => __('Heading Line 2', 'synthetic-nature'),
        'section' => 'sn_hero',
        'type'    => 'text',
    ]);

    // Subtitle
    $wp_customize->add_setting('sn_subtitle', [
        'default'           => 'An odyssey through delicate living forms, revealed by lens and curiosity.',
        'sanitize_callback' => 'wp_kses_post',
        'transport'         => 'postMessage',
    ]);
    $wp_customize->add_control('sn_subtitle', [
        'label'   => __('Subtitle / Description', 'synthetic-nature'),
        'section' => 'sn_hero',
        'type'    => 'textarea',
    ]);

    // CTA text
    $wp_customize->add_setting('sn_cta_text', [
        'default'           => 'Begin the Experience',
        'sanitize_callback' => 'sanitize_text_field',
        'transport'         => 'postMessage',
    ]);
    $wp_customize->add_control('sn_cta_text', [
        'label'   => __('Button Text', 'synthetic-nature'),
        'section' => 'sn_hero',
        'type'    => 'text',
    ]);

    // CTA URL
    $wp_customize->add_setting('sn_cta_url', [
        'default'           => '#',
        'sanitize_callback' => 'esc_url_raw',
    ]);
    $wp_customize->add_control('sn_cta_url', [
        'label'   => __('Button Link URL', 'synthetic-nature'),
        'section' => 'sn_hero',
        'type'    => 'url',
    ]);

    // ── Section: Video ───────────────────────────────
    $wp_customize->add_section('sn_video', [
        'title' => __('Background Video', 'synthetic-nature'),
        'panel' => 'sn_panel',
    ]);
    $wp_customize->add_setting('sn_video_url', [
        'default'           => 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260619_191346_9d19d66e-86a4-47f7-8dc6-712c1788c3b2.mp4',
        'sanitize_callback' => 'esc_url_raw',
    ]);
    $wp_customize->add_control('sn_video_url', [
        'label'       => __('Video URL (.mp4)', 'synthetic-nature'),
        'description' => __('Paste a direct link to your background video (MP4).', 'synthetic-nature'),
        'section'     => 'sn_video',
        'type'        => 'url',
    ]);
}
add_action('customize_register', 'sn_customizer');

/* ══════════════════════════════
   Live preview (postMessage)
══════════════════════════════ */
function sn_customizer_preview_js() {
    wp_enqueue_script(
        'sn-customizer-preview',
        get_template_directory_uri() . '/assets/js/customizer-preview.js',
        ['customize-preview'], '1.0', true
    );
}
add_action('customize_preview_init', 'sn_customizer_preview_js');

/* ══════════════════════════════
   Helper: get customizer value
══════════════════════════════ */
function sn_get(string $key, string $fallback = ''): string {
    return (string) get_theme_mod($key, $fallback);
}

/* ══════════════════════════════
   Fallback nav (no menu assigned)
══════════════════════════════ */
function sn_fallback_nav(): void {
    $links = ['Wander' => '#', 'Archive' => '#', 'Story' => '#', 'Connect' => '#'];
    echo '<ul class="sn-nav-links">';
    foreach ($links as $label => $url) {
        printf('<li><a href="%s">%s</a></li>', esc_url($url), esc_html($label));
    }
    echo '</ul>';
}
