import 'dart:ui';
import 'package:flutter/material.dart';

/// Modern effects utility class for glass morphism and neon glow effects
class ModernEffects {
  /// Glass card shadow effects
  static List<BoxShadow> glassCardShadows() {
    return [
      BoxShadow(
        color: Colors.black.withOpacity(0.1),
        blurRadius: 20,
        offset: const Offset(0, 8),
      ),
      BoxShadow(
        color: Colors.black.withOpacity(0.05),
        blurRadius: 10,
        offset: const Offset(0, 2),
      ),
    ];
  }

  /// Backdrop filter for glass morphism effect
  static ImageFilter get backdropFilter {
    return ImageFilter.blur(sigmaX: 10, sigmaY: 10);
  }

  /// Neon glow shadows for status indicators
  static List<BoxShadow> neonGlowShadows(Color color) {
    return [
      BoxShadow(
        color: color.withOpacity(0.6),
        blurRadius: 20,
        spreadRadius: 2,
      ),
      BoxShadow(
        color: color.withOpacity(0.3),
        blurRadius: 40,
        spreadRadius: 4,
      ),
    ];
  }

  /// Cyan neon glow (primary)
  static List<BoxShadow> get cyanGlow {
    return neonGlowShadows(const Color(0xFF00FFFF));
  }

  /// Green neon glow (success)
  static List<BoxShadow> get greenGlow {
    return neonGlowShadows(const Color(0xFF00FF7F));
  }

  /// Orange neon glow (warning)
  static List<BoxShadow> get orangeGlow {
    return neonGlowShadows(const Color(0xFFFFA500));
  }

  /// Red neon glow (error)
  static List<BoxShadow> get redGlow {
    return neonGlowShadows(const Color(0xFFFF0000));
  }

  /// Holographic border decoration
  static BoxDecoration holographicBorder({
    Color borderColor = const Color(0xFF00FFFF),
    double borderWidth = 1.5,
    double blurRadius = 10,
  }) {
    return BoxDecoration(
      border: Border.all(
        color: borderColor.withOpacity(0.5),
        width: borderWidth,
      ),
      borderRadius: BorderRadius.circular(12),
      boxShadow: [
        BoxShadow(
          color: borderColor.withOpacity(0.3),
          blurRadius: blurRadius,
          spreadRadius: 1,
        ),
      ],
    );
  }

  /// Glass morphism container decoration
  static BoxDecoration glassContainer({
    Color color = const Color(0xFF0A0E27),
    double opacity = 0.05,
    double borderRadius = 12,
  }) {
    return BoxDecoration(
      color: color.withOpacity(opacity),
      borderRadius: BorderRadius.circular(borderRadius),
      border: Border.all(
        color: const Color(0xFF00FFFF).withOpacity(0.2),
        width: 1,
      ),
      boxShadow: glassCardShadows(),
    );
  }

  /// Animated pulse effect configuration
  static Future<void> animatePulse(
    AnimationController controller, {
    Duration duration = const Duration(milliseconds: 1500),
  }) async {
    controller.repeat(
      min: 0.8,
      max: 1.0,
      period: duration,
      reverse: true,
    );
  }

  /// Get color based on status
  static Color statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'active':
      case 'success':
        return const Color(0xFF00FF7F); // Green
      case 'idle':
      case 'pending':
        return const Color(0xFF00FFFF); // Cyan
      case 'error':
      case 'failed':
        return const Color(0xFFFF0000); // Red
      case 'warning':
        return const Color(0xFFFFA500); // Orange
      default:
        return const Color(0xFF00FFFF); // Default cyan
    }
  }

  /// Get glow shadow based on status
  static List<BoxShadow> statusGlow(String status) {
    return neonGlowShadows(statusColor(status));
  }
}
