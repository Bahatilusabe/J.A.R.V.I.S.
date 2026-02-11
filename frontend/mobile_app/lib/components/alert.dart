import 'package:flutter/material.dart';
import '../theme.dart';
import '../utils/modern_effects.dart';

/// Alert variant enum - matches React CVA pattern
enum AlertVariant {
  default_,
  destructive,
  warning,
  success,
  info,
}

/// Extension to get alert variant properties
extension AlertVariantProps on AlertVariant {
  Color get backgroundColor {
    switch (this) {
      case AlertVariant.default_:
        return Colors.white.withValues(alpha: 0.03);
      case AlertVariant.destructive:
        return neonRed.withValues(alpha: 0.1);
      case AlertVariant.warning:
        return neonOrange.withValues(alpha: 0.1);
      case AlertVariant.success:
        return quantumGreen.withValues(alpha: 0.1);
      case AlertVariant.info:
        return holographicBlue.withValues(alpha: 0.1);
    }
  }

  Color get borderColor {
    switch (this) {
      case AlertVariant.default_:
        return Colors.white.withValues(alpha: 0.2);
      case AlertVariant.destructive:
        return neonRed.withValues(alpha: 0.5);
      case AlertVariant.warning:
        return neonOrange.withValues(alpha: 0.5);
      case AlertVariant.success:
        return quantumGreen.withValues(alpha: 0.5);
      case AlertVariant.info:
        return holographicBlue.withValues(alpha: 0.5);
    }
  }

  Color get textColor {
    switch (this) {
      case AlertVariant.default_:
        return Colors.white;
      case AlertVariant.destructive:
        return neonRed;
      case AlertVariant.warning:
        return neonOrange;
      case AlertVariant.success:
        return quantumGreen;
      case AlertVariant.info:
        return holographicBlue;
    }
  }

  Color get iconColor {
    switch (this) {
      case AlertVariant.default_:
        return Colors.white.withValues(alpha: 0.7);
      case AlertVariant.destructive:
        return neonRed;
      case AlertVariant.warning:
        return neonOrange;
      case AlertVariant.success:
        return quantumGreen;
      case AlertVariant.info:
        return holographicBlue;
    }
  }

  bool get hasGlow {
    return this == AlertVariant.destructive ||
        this == AlertVariant.warning ||
        this == AlertVariant.success ||
        this == AlertVariant.info;
  }

  List<BoxShadow> get glowEffect {
    final color = textColor;
    if (!hasGlow) return [];
    return [
      BoxShadow(
        color: color.withValues(alpha: 0.3),
        blurRadius: 8,
        spreadRadius: 0,
      ),
      BoxShadow(
        color: color.withValues(alpha: 0.15),
        blurRadius: 16,
        spreadRadius: 2,
      ),
    ];
  }
}

/// Reusable Alert component - Glass morphism with neon glow
/// Equivalent to React's Alert component with CVA variants
class Alert extends StatelessWidget {
  final Widget child;
  final AlertVariant variant;
  final EdgeInsets padding;
  final BorderRadius borderRadius;
  final bool showBorder;
  final VoidCallback? onDismiss;
  final double elevation;

  const Alert({
    Key? key,
    required this.child,
    this.variant = AlertVariant.default_,
    this.padding = const EdgeInsets.all(16),
    this.borderRadius = const BorderRadius.all(Radius.circular(12)),
    this.showBorder = true,
    this.onDismiss,
    this.elevation = 0,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isMobile = MediaQuery.of(context).size.width < 600;

    return Container(
      decoration: BoxDecoration(
        color: variant.backgroundColor,
        border: showBorder
            ? Border.all(
                color: variant.borderColor,
                width: 1,
              )
            : null,
        borderRadius: borderRadius,
        boxShadow: [
          ...ModernEffects.glassCardShadows(),
          ...variant.glowEffect,
        ],
      ),
      child: ClipRRect(
        borderRadius: borderRadius,
        child: BackdropFilter(
          filter: ModernEffects.backdropFilter,
          child: Padding(
            padding: padding,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Icon placeholder - 40x40
                    SizedBox(
                      width: 40,
                      height: 40,
                      child: Padding(
                        padding: const EdgeInsets.only(right: 12),
                        child: Icon(
                          _getIconForVariant(),
                          color: variant.iconColor,
                      size: 20,
                    ),
                  ),
                ),
                // Content area
                Expanded(
                  child: child,
                ),
                // Dismiss button
                if (onDismiss != null)
                  GestureDetector(
                    onTap: onDismiss,
                    child: Padding(
                      padding: const EdgeInsets.only(left: 8),
                      child: Icon(
                        Icons.close,
                        color: variant.textColor,
                        size: 20,
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
          ),
        ),
      ),
    );
  }

  IconData _getIconForVariant() {
    switch (variant) {
      case AlertVariant.default_:
        return Icons.info_outlined;
      case AlertVariant.destructive:
        return Icons.error_outline;
      case AlertVariant.warning:
        return Icons.warning_outlined;
      case AlertVariant.success:
        return Icons.check_circle_outline;
      case AlertVariant.info:
        return Icons.info_outlined;
    }
  }
}

/// Alert Title component - Equivalent to React's AlertTitle
class AlertTitle extends StatelessWidget {
  final String text;
  final TextStyle? style;
  final Color? color;

  const AlertTitle(
    this.text, {
    Key? key,
    this.style,
    this.color,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: (style ?? const TextStyle()).copyWith(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        color: color ?? Colors.white,
        letterSpacing: 0.3,
      ),
    );
  }
}

/// Alert Description component - Equivalent to React's AlertDescription
class AlertDescription extends StatelessWidget {
  final String text;
  final TextStyle? style;
  final Color? color;

  const AlertDescription(
    this.text, {
    Key? key,
    this.style,
    this.color,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Text(
        text,
        style: (style ?? const TextStyle()).copyWith(
          fontSize: 13,
          color: color ?? Colors.white70,
          height: 1.5,
          letterSpacing: 0.2,
        ),
      ),
    );
  }
}

/// Reusable Alert content container
class AlertContent extends StatelessWidget {
  final AlertTitle title;
  final AlertDescription description;
  final AlertVariant variant;

  const AlertContent({
    Key? key,
    required this.title,
    required this.description,
    this.variant = AlertVariant.default_,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        AlertTitle(
          title.text,
          color: variant.textColor,
        ),
        AlertDescription(
          description.text,
          color: variant.textColor.withValues(alpha: 0.8),
        ),
      ],
    );
  }
}

/// Advanced Alert with action buttons
class AlertWithAction extends StatelessWidget {
  final AlertVariant variant;
  final AlertTitle title;
  final AlertDescription description;
  final List<AlertAction> actions;
  final VoidCallback? onDismiss;
  final EdgeInsets padding;

  const AlertWithAction({
    Key? key,
    required this.title,
    required this.description,
    this.variant = AlertVariant.default_,
    this.actions = const [],
    this.onDismiss,
    this.padding = const EdgeInsets.all(16),
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Alert(
      variant: variant,
      padding: padding,
      onDismiss: onDismiss,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          AlertContent(
            title: title,
            description: description,
            variant: variant,
          ),
          if (actions.isNotEmpty) ...[
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: actions
                  .asMap()
                  .entries
                  .map((e) => Padding(
                        padding: EdgeInsets.only(
                          left: e.key > 0 ? 8 : 0,
                        ),
                        child: _buildActionButton(e.value, variant),
                      ))
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildActionButton(AlertAction action, AlertVariant variant) {
    final isDestructive = action.isDestructive;
    final color = isDestructive ? neonRed : variant.textColor;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: action.onPressed,
        borderRadius: BorderRadius.circular(6),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            border: Border.all(
              color: color.withValues(alpha: 0.3),
              width: 0.5,
            ),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            action.label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: color,
              letterSpacing: 0.2,
            ),
          ),
        ),
      ),
    );
  }
}

/// Alert action model
class AlertAction {
  final String label;
  final VoidCallback onPressed;
  final bool isDestructive;

  AlertAction({
    required this.label,
    required this.onPressed,
    this.isDestructive = false,
  });
}
