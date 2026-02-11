import 'package:flutter_riverpod/flutter_riverpod.dart';

// Example provider: current selected mobile shell index
final mobileIndexProvider = StateProvider<int>((ref) => 0);

// Add additional providers here as the app grows (auth state, ws clients, data caches)
