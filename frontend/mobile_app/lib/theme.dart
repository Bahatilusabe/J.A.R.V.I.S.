import 'package:flutter/material.dart';

// ═══════════════════════════════════════════════════════════════════════════
// HOLOGRAPHIC NEON COLOR PALETTE - Cutting-Edge Modern Design
// ═══════════════════════════════════════════════════════════════════════════

// Primary Colors
const Color neonCyan = Color(0xFF00E8FF);           // Primary action, glows, alerts
const Color deepSpaceNavy = Color(0xFF0A0E27);     // Background
const Color holographicBlue = Color(0xFF0099FF);   // Secondary, accents

// Status Colors - Vibrant Neon
const Color quantumGreen = Color(0xFF00FF88);      // Success, threats contained
const Color neonOrange = Color(0xFFFFB800);        // Warning, caution
const Color neonRed = Color(0xFFFF3366);           // Danger, critical

// Neutral Colors
const Color cardBackground = Color.fromARGB(13, 255, 255, 255); // Glass effect rgba(255,255,255,0.05)
const Color textPrimary = Color(0xFFE0E8FF);       // High contrast
const Color textSecondary = Color(0xFFA0B0C8);     // Reduced emphasis
const Color borderColor = Color.fromARGB(51, 0, 232, 255); // Holographic border rgba(0,232,255,0.2)

// ═══════════════════════════════════════════════════════════════════════════
// MODERN THEME - Glass Morphism + Holographic Neon
// ═══════════════════════════════════════════════════════════════════════════

final ThemeData jarvisTheme = ThemeData(
  useMaterial3: true,
  brightness: Brightness.dark,
  
  // Deep navy background - primary canvas
  scaffoldBackgroundColor: deepSpaceNavy,
  canvasColor: deepSpaceNavy,
  
  // Primary & Accent Colors - Holographic Neon
  colorScheme: const ColorScheme.dark(
    primary: neonCyan,
    secondary: holographicBlue,
    tertiary: quantumGreen,
    surface: cardBackground,
    surfaceContainer: cardBackground,
    error: neonRed,
    onPrimary: deepSpaceNavy,
    onSecondary: deepSpaceNavy,
    onSurface: textPrimary,
  ),
  
  // AppBar - Modern Glass Effect
  appBarTheme: const AppBarTheme(
    backgroundColor: cardBackground,
    foregroundColor: neonCyan,
    elevation: 0,
    centerTitle: false,
    titleTextStyle: TextStyle(
      fontSize: 20,
      fontWeight: FontWeight.w600,
      color: textPrimary,
      letterSpacing: 0.3,
    ),
  ),
  
  // Cards - Glass Morphism with Holographic Border
  cardTheme: CardThemeData(
    color: cardBackground,
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(8),
      side: const BorderSide(color: borderColor, width: 1),
    ),
    clipBehavior: Clip.antiAlias,
  ),
  
  // ───────────────────────────────────────────────────────────────────────
  // TYPOGRAPHY - Modern Stack with Professional Spacing
  // ───────────────────────────────────────────────────────────────────────
  
  textTheme: const TextTheme(
    // Display styles - Large headings
    displayLarge: TextStyle(
      fontSize: 32,
      fontWeight: FontWeight.w700,
      color: textPrimary,
      letterSpacing: 0.3,
      height: 1.5,
    ),
    displayMedium: TextStyle(
      fontSize: 28,
      fontWeight: FontWeight.w600,
      color: textPrimary,
      letterSpacing: 0.3,
      height: 1.5,
    ),
    
    // Headline styles - Section headings
    headlineLarge: TextStyle(
      fontSize: 24,
      fontWeight: FontWeight.w600,
      color: textPrimary,
      letterSpacing: 0.3,
      height: 1.5,
    ),
    headlineMedium: TextStyle(
      fontSize: 20,
      fontWeight: FontWeight.w600,
      color: textPrimary,
      letterSpacing: 0.3,
      height: 1.5,
    ),
    headlineSmall: TextStyle(
      fontSize: 18,
      fontWeight: FontWeight.w600,
      color: textPrimary,
      letterSpacing: 0.3,
      height: 1.5,
    ),
    
    // Body styles - Main content
    bodyLarge: TextStyle(
      fontSize: 16,
      fontWeight: FontWeight.w500,
      color: textPrimary,
      height: 1.5,
      letterSpacing: 0.3,
    ),
    bodyMedium: TextStyle(
      fontSize: 14,
      fontWeight: FontWeight.w400,
      color: textPrimary,
      height: 1.5,
      letterSpacing: 0.3,
    ),
    bodySmall: TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w400,
      color: textSecondary,
      height: 1.5,
      letterSpacing: 0.3,
    ),
    
    // Label styles - Buttons, chips, badges
    labelLarge: TextStyle(
      fontSize: 14,
      fontWeight: FontWeight.w600,
      color: neonCyan,
      letterSpacing: 0.5,
    ),
    labelMedium: TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w600,
      color: neonCyan,
      letterSpacing: 0.5,
    ),
    labelSmall: TextStyle(
      fontSize: 11,
      fontWeight: FontWeight.w600,
      color: neonCyan,
      letterSpacing: 0.5,
    ),
  ),
  
  // ───────────────────────────────────────────────────────────────────────
  // BUTTONS - Modern Interactive Style with Glow
  // ───────────────────────────────────────────────────────────────────────
  
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: neonCyan,
      foregroundColor: deepSpaceNavy,
      elevation: 0,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      textStyle: const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
      ),
    ),
  ),
  
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: neonCyan,
      side: const BorderSide(color: neonCyan, width: 1.5),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      textStyle: const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
      ),
    ),
  ),
  
  textButtonTheme: TextButtonThemeData(
    style: TextButton.styleFrom(
      foregroundColor: neonCyan,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      textStyle: const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
      ),
    ),
  ),
  
  // ───────────────────────────────────────────────────────────────────────
  // INPUT DECORATION - Glass Effect with Modern Focus Ring
  // ───────────────────────────────────────────────────────────────────────
  
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: const Color.fromARGB(77, 0, 0, 0), // Dark glass effect
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: const BorderSide(color: borderColor, width: 1),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: const BorderSide(color: borderColor, width: 1),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: const BorderSide(color: neonCyan, width: 2),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: const BorderSide(color: neonRed, width: 1),
    ),
    focusedErrorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: const BorderSide(color: neonRed, width: 2),
    ),
    hintStyle: const TextStyle(
      color: textSecondary,
      letterSpacing: 0.3,
      fontSize: 14,
    ),
    labelStyle: const TextStyle(
      color: neonCyan,
      letterSpacing: 0.3,
      fontWeight: FontWeight.w500,
    ),
    prefixIconColor: MaterialStateColor.resolveWith((states) {
      return states.contains(MaterialState.focused) ? neonCyan : textSecondary;
    }),
  ),
  
  // ───────────────────────────────────────────────────────────────────────
  // BOTTOM NAVIGATION - Modern Style with Glass Background
  // ───────────────────────────────────────────────────────────────────────
  
  bottomNavigationBarTheme: const BottomNavigationBarThemeData(
    backgroundColor: cardBackground,
    selectedItemColor: neonCyan,
    unselectedItemColor: textSecondary,
    type: BottomNavigationBarType.fixed,
    elevation: 0,
    selectedLabelStyle: TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.3,
    ),
    unselectedLabelStyle: TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w400,
      letterSpacing: 0.3,
    ),
  ),
  
  // ───────────────────────────────────────────────────────────────────────
  // DIVIDERS & BORDERS - Subtle Holographic Effects
  // ───────────────────────────────────────────────────────────────────────
  
  dividerTheme: const DividerThemeData(
    color: borderColor,
    thickness: 1,
    space: 16,
  ),
  
  // ───────────────────────────────────────────────────────────────────────
  // ICONS - Neon Cyan Default
  // ───────────────────────────────────────────────────────────────────────
  
  iconTheme: const IconThemeData(
    color: neonCyan,
    size: 24,
  ),
  
  // Snackbars - Modern with Holographic Design
  snackBarTheme: SnackBarThemeData(
    backgroundColor: cardBackground,
    contentTextStyle: const TextStyle(
      color: textPrimary,
      letterSpacing: 0.3,
    ),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(8),
      side: const BorderSide(color: borderColor, width: 1),
    ),
  ),
);
