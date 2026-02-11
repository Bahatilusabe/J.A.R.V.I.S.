import 'dart:ui';
import 'package:flutter/material.dart';
import '../theme.dart';

/// Modern visual effects and utilities for cutting-edge UI
class ModernEffects {
  /// Glass Morphism Card Container
  static BoxDecoration glassCard({
    double blur = 10,
    double opacity = 0.05,
    bool hasGlow = false,
  }) {
    return BoxDecoration(
      color: cardBackground,
      borderRadius: BorderRadius.circular(8),
      border: Border.all(color: borderColor, width: 1),
      boxShadow: hasGlow
          ? [
              BoxShadow(
                color: neonCyan.withValues(alpha: 0.3),
                blurRadius: 20,
                spreadRadius: 0,
              ),
              BoxShadow(
                color: neonCyan.withValues(alpha: 0.1),
                blurRadius: 40,
                spreadRadius: 4,
              ),
            ]
          : null,
    );
  }

  /// Neon Glow Effect - Holographic
  static BoxDecoration neonGlow({
    Color color = neonCyan,
    double intensity = 0.5,
  }) {
    return BoxDecoration(
      boxShadow: [
        BoxShadow(
          color: color.withValues(alpha: intensity * 0.5),
          blurRadius: 10,
          spreadRadius: 0,
        ),
        BoxShadow(
          color: color.withValues(alpha: intensity * 0.3),
          blurRadius: 20,
          spreadRadius: 2,
        ),
      ],
    );
  }

  /// Neon Glow Shadow List (for use in boxShadow property)
  static List<BoxShadow> neonGlowShadows({
    Color color = neonCyan,
    double intensity = 0.5,
  }) {
    return [
      BoxShadow(
        color: color.withValues(alpha: intensity * 0.5),
        blurRadius: 10,
        spreadRadius: 0,
      ),
      BoxShadow(
        color: color.withValues(alpha: intensity * 0.3),
        blurRadius: 20,
        spreadRadius: 2,
      ),
    ];
  }

  /// Holographic Text Gradient
  static ShaderMask holographicText(
    Widget child, {
    List<Color>? colors,
  }) {
    final gradientColors = colors ??
        [
          neonCyan,
          holographicBlue,
          quantumGreen,
        ];

    return ShaderMask(
      shaderCallback: (bounds) {
        return LinearGradient(
          colors: gradientColors,
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ).createShader(bounds);
      },
      child: child,
    );
  }

  /// Modern Card with Interactive Effects
  static Widget interactiveCard({
    required Widget child,
    required VoidCallback onTap,
    double elevationOnHover = 20,
    bool enableGlow = true,
  }) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          decoration: ModernEffects.glassCard(hasGlow: enableGlow),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: onTap,
              splashColor: neonCyan.withValues(alpha: 0.1),
              highlightColor: neonCyan.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(8),
              child: child,
            ),
          ),
        ),
      ),
    );
  }

  /// Neon Pulse Animation (continuous glow)
  static Animation<double> createPulseAnimation(
    AnimationController controller,
  ) {
    return Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(
        parent: controller,
        curve: Curves.easeInOut,
      ),
    );
  }

  /// Create a modern text style with glow effect
  static TextStyle glowingTextStyle({
    required TextStyle baseStyle,
    Color glowColor = neonCyan,
  }) {
    return baseStyle.copyWith(
      shadows: [
        Shadow(
          color: glowColor.withValues(alpha: 0.5),
          blurRadius: 8,
        ),
      ],
    );
  }

  /// Gradient Background - Subtle Cyberpunk
  static BoxDecoration gradientBackground() {
    return BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          deepSpaceNavy,
          deepSpaceNavy.withValues(alpha: 0.95),
          holographicBlue.withValues(alpha: 0.05),
        ],
      ),
    );
  }

  /// Status Badge - Modern with Glow
  static Widget statusBadge({
    required String label,
    required Color color,
    bool enableGlow = true,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        border: Border.all(color: color.withValues(alpha: 0.6), width: 1),
        borderRadius: BorderRadius.circular(20),
        boxShadow: enableGlow
            ? [
                BoxShadow(
                  color: color.withValues(alpha: 0.3),
                  blurRadius: 8,
                  spreadRadius: 0,
                ),
              ]
            : null,
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.5,
        ),
      ),
    );
  }

  /// Modern Button with Neon Glow
  static Widget glowButton({
    required String label,
    required VoidCallback onPressed,
    Color buttonColor = neonCyan,
    Color textColor = deepSpaceNavy,
    bool isPrimary = true,
  }) {
    return Container(
      decoration: isPrimary ? ModernEffects.neonGlow(color: buttonColor) : null,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: isPrimary ? buttonColor : Colors.transparent,
          foregroundColor: isPrimary ? textColor : buttonColor,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          side: !isPrimary
              ? BorderSide(color: buttonColor, width: 1.5)
              : BorderSide.none,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  /// Smooth Fade-in Animation
  static Widget fadeIn({
    required Widget child,
    Duration duration = const Duration(milliseconds: 300),
  }) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: duration,
      curve: Curves.easeOut,
      builder: (context, value, child) {
        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(0, 10 * (1 - value)),
            child: child,
          ),
        );
      },
      child: child,
    );
  }

  /// Slide-in Animation from Left
  static Widget slideInFromLeft({
    required Widget child,
    Duration duration = const Duration(milliseconds: 400),
  }) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: -20, end: 0),
      duration: duration,
      curve: Curves.easeOut,
      builder: (context, value, child) {
        return Opacity(
          opacity: (value + 20) / 20,
          child: Transform.translate(
            offset: Offset(value, 0),
            child: child,
          ),
        );
      },
      child: child,
    );
  }

  /// Scale & Glow on Hover Effect
  static Widget scalableCard({
    required Widget child,
    double scale = 1.02,
    Duration duration = const Duration(milliseconds: 300),
  }) {
    return MouseRegion(
      onEnter: (_) {},
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 1, end: 1),
        duration: duration,
        builder: (context, value, child) {
          return Transform.scale(
            scale: value,
            child: child,
          );
        },
        child: child,
      ),
    );
  }

  /// Glass card shadow effects
  static List<BoxShadow> glassCardShadows() {
    return [
      BoxShadow(
        color: Colors.black.withValues(alpha: 0.1),
        blurRadius: 20,
        offset: const Offset(0, 8),
      ),
      BoxShadow(
        color: Colors.black.withValues(alpha: 0.05),
        blurRadius: 10,
        offset: const Offset(0, 2),
      ),
    ];
  }

  /// Backdrop filter for glass morphism effect
  static ImageFilter get backdropFilter {
    return ImageFilter.blur(sigmaX: 10, sigmaY: 10);
  }
}
