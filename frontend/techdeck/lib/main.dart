import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';

import 'package:techdeck/homepage.dart';

void main() {
  runApp(const TechDeckApp());
}

class TechDeckApp extends StatelessWidget {
  const TechDeckApp({super.key});

  @override
  Widget build(BuildContext context) {
    ColorScheme colorScheme = ColorScheme.fromSeed(seedColor: Colors.red);

    return MaterialApp(
      title: 'Tech Deck',
      theme: ThemeData.dark(),
      home: const TechDeckHomePage(),
    );
  }
}