import 'package:flutter/material.dart';

class VocalSocView extends StatelessWidget {
  const VocalSocView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('VocalSOC')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(children: [
          const Text('Live ASR & Actions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(children: const [
                Icon(Icons.mic, size: 48, color: Colors.cyan),
                SizedBox(height: 8),
                Text('Waveform / live transcript will appear here.'),
              ]),
            ),
          ),
          const SizedBox(height: 12),
          ElevatedButton(onPressed: () {}, child: const Text('Start ASR (stub)'))
        ]),
      ),
    );
  }
}
