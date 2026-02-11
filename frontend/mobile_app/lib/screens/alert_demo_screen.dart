import 'package:flutter/material.dart';
import '../components/alert.dart';
import '../theme.dart';

/// Demo screen showing Alert component usage
/// This demonstrates the innovative Dart/Flutter implementation
/// of the React CVA-based Alert pattern
class AlertDemoScreen extends StatefulWidget {
  const AlertDemoScreen({Key? key}) : super(key: key);

  @override
  State<AlertDemoScreen> createState() => _AlertDemoScreenState();
}

class _AlertDemoScreenState extends State<AlertDemoScreen> {
  bool _showDefault = true;
  bool _showDestructive = true;
  bool _showWarning = true;
  bool _showSuccess = true;
  bool _showInfo = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Alert Components - JARVIS Design System'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title
            const Text(
              'Alert Components',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Reusable alert components with glass morphism and neon glow effects',
              style: TextStyle(
                fontSize: 13,
                color: Colors.white.withValues(alpha: 0.7),
              ),
            ),
            const SizedBox(height: 24),

            // Default Alert
            if (_showDefault)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Alert(
                  variant: AlertVariant.default_,
                  onDismiss: () => setState(() => _showDefault = false),
                  child: AlertContent(
                    title: AlertTitle('Default Alert'),
                    description: AlertDescription(
                      'This is a default alert with informational styling',
                    ),
                    variant: AlertVariant.default_,
                  ),
                ),
              ),

            // Destructive Alert
            if (_showDestructive)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Alert(
                  variant: AlertVariant.destructive,
                  onDismiss: () => setState(() => _showDestructive = false),
                  child: AlertContent(
                    title: AlertTitle('Destructive Alert'),
                    description: AlertDescription(
                      'This alert indicates a critical error or destructive action',
                    ),
                    variant: AlertVariant.destructive,
                  ),
                ),
              ),

            // Warning Alert
            if (_showWarning)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Alert(
                  variant: AlertVariant.warning,
                  onDismiss: () => setState(() => _showWarning = false),
                  child: AlertContent(
                    title: AlertTitle('Warning Alert'),
                    description: AlertDescription(
                      'This alert warns about potential issues that need attention',
                    ),
                    variant: AlertVariant.warning,
                  ),
                ),
              ),

            // Success Alert
            if (_showSuccess)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Alert(
                  variant: AlertVariant.success,
                  onDismiss: () => setState(() => _showSuccess = false),
                  child: AlertContent(
                    title: AlertTitle('Success Alert'),
                    description: AlertDescription(
                      'Operation completed successfully with all systems nominal',
                    ),
                    variant: AlertVariant.success,
                  ),
                ),
              ),

            // Info Alert
            if (_showInfo)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Alert(
                  variant: AlertVariant.info,
                  onDismiss: () => setState(() => _showInfo = false),
                  child: AlertContent(
                    title: AlertTitle('Info Alert'),
                    description: AlertDescription(
                      'Additional information that might be useful',
                    ),
                    variant: AlertVariant.info,
                  ),
                ),
              ),

            const SizedBox(height: 24),
            const Divider(),
            const SizedBox(height: 24),

            // Advanced Alert with Actions
            const Text(
              'Advanced Alert with Actions',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 16),

            AlertWithAction(
              variant: AlertVariant.warning,
              title: AlertTitle('System Warning'),
              description: AlertDescription(
                'Unusual activity detected in the forensics system. Review immediately?',
              ),
              actions: [
                AlertAction(
                  label: 'Dismiss',
                  onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Alert dismissed')),
                  ),
                ),
                AlertAction(
                  label: 'Review Now',
                  onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Navigating to forensics...')),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 24),

            AlertWithAction(
              variant: AlertVariant.destructive,
              title: AlertTitle('Critical Threat Detected'),
              description: AlertDescription(
                'A critical security threat has been identified in the attack surface. Immediate action required.',
              ),
              actions: [
                AlertAction(
                  label: 'Contain',
                  onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Initiating containment...')),
                  ),
                ),
                AlertAction(
                  label: 'Investigate',
                  onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Opening investigation panel...')),
                  ),
                ),
                AlertAction(
                  label: 'Escalate',
                  onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Escalating to SOC...')),
                  ),
                  isDestructive: true,
                ),
              ],
            ),

            const SizedBox(height: 24),

            AlertWithAction(
              variant: AlertVariant.success,
              title: AlertTitle('Threat Contained'),
              description: AlertDescription(
                'The detected threat has been successfully neutralized and quarantined.',
              ),
              actions: [
                AlertAction(
                  label: 'View Report',
                  onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Opening forensics report...')),
                  ),
                ),
                AlertAction(
                  label: 'Close',
                  onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Alert closed')),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}
