import 'package:flutter/material.dart';

class PasmFullView extends StatelessWidget {
  const PasmFullView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('PASM — Temporal Viewer')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(mainAxisSize: MainAxisSize.min, children: const [
            Icon(Icons.timeline, size: 48, color: Colors.cyan),
            SizedBox(height: 12),
            Text('Full PASM temporal graph will render here.', textAlign: TextAlign.center),
          ]),
        ),
      ),
    );
  }
}
