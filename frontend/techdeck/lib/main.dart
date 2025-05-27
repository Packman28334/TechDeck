import 'package:flutter/material.dart';
import 'package:techdeck/homepage.dart';

void main() {
  runApp(const TechDeckApp());
}

class TechDeckApp extends StatelessWidget {
  const TechDeckApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Tech Deck',
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorSchemeSeed: Colors.red,
      ),
      home: const TechDeckHomePage(),
    );
  }
}