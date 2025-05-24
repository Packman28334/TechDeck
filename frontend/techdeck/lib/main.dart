import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import 'package:techdeck/homepage.dart';

void main() {
  runApp(const TechDeckApp());
}

class TechDeckApp extends StatelessWidget {
  const TechDeckApp({super.key});

  @override
  Widget build(BuildContext context) {
    ColorScheme colorScheme = ColorScheme.fromSeed(seedColor: Colors.red);

    return CupertinoApp(
      title: 'Tech Deck',
      theme: CupertinoThemeData(),
      home: const TechDeckHomePage(),
    );
  }
}