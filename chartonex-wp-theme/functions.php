<?php
/**
 * Chartonex Theme — functions.php
 */

defined('ABSPATH') || exit;

define('CX_VERSION', '1.0.0');
define('CX_URI',     get_template_directory_uri());

/* ── Enqueue styles & scripts ── */
function chartonex_enqueue() {
    // Google Fonts
    wp_enqueue_style(
        'cx-fonts',
        'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap',
        [],
        null
    );
    // Main stylesheet
    wp_enqueue_style(
        'cx-main',
        CX_URI . '/assets/css/chartonex.css',
        ['cx-fonts'],
        CX_VERSION
    );
    // WordPress default style (kept for admin bar)
    wp_enqueue_style('wp-block-library', false);

    // Main JS (deferred)
    wp_enqueue_script(
        'cx-main',
        CX_URI . '/assets/js/chartonex.js',
        [],
        CX_VERSION,
        true
    );
    wp_script_add_data('cx-main', 'defer', true);
}
add_action('wp_enqueue_scripts', 'chartonex_enqueue');

/* ── Theme supports ── */
function chartonex_setup() {
    add_theme_support('title-tag');
    add_theme_support('custom-logo');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['script', 'style', 'search-form']);
    add_theme_support('responsive-embeds');

    register_nav_menus([
        'primary' => __('Primary Navigation', 'chartonex'),
        'footer'  => __('Footer Navigation', 'chartonex'),
    ]);
}
add_action('after_setup_theme', 'chartonex_setup');

/* ── Body class for dark bg ── */
function chartonex_body_classes($classes) {
    if (is_front_page() || is_page_template('templates/landing.php')) {
        $classes[] = 'chartonex-page';
    }
    return $classes;
}
add_filter('body_class', 'chartonex_body_classes');

/* ── Remove emoji scripts (performance) ── */
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('wp_print_styles', 'print_emoji_styles');

/* ── Remove WP block styles not needed ── */
function chartonex_remove_block_styles() {
    if (is_front_page()) {
        wp_dequeue_style('wp-block-library');
        wp_dequeue_style('wp-block-library-theme');
        wp_dequeue_style('classic-theme-styles');
    }
}
add_action('wp_enqueue_scripts', 'chartonex_remove_block_styles', 100);

/* ── Shortcode: [chartonex_landing] — embeds the full page content ── */
function chartonex_landing_shortcode() {
    ob_start();
    include get_template_directory() . '/templates/landing-content.php';
    return ob_get_clean();
}
add_shortcode('chartonex_landing', 'chartonex_landing_shortcode');

/* ── Customizer options ── */
function chartonex_customizer($wp_customize) {
    $wp_customize->add_section('chartonex_hero', [
        'title'    => __('Hero Section', 'chartonex'),
        'priority' => 30,
    ]);

    $fields = [
        ['chartonex_hero_title',    'Hero Title',    'Trade Smarter. Go Beyond the Charts.'],
        ['chartonex_hero_subtitle', 'Hero Subtitle', 'Chartonex combines advanced market analysis, AI-driven signals, and real-time intelligence for crypto, gold, and forex — all in one unified platform.'],
        ['chartonex_hero_cta',      'CTA Button Text','Start Trading Now'],
    ];

    foreach ($fields as [$id, $label, $default]) {
        $wp_customize->add_setting($id, ['default' => $default, 'sanitize_callback' => 'sanitize_text_field']);
        $wp_customize->add_control($id, ['label' => __($label, 'chartonex'), 'section' => 'chartonex_hero', 'type' => 'text']);
    }
}
add_action('customize_register', 'chartonex_customizer');
