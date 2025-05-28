import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';
import 'package:techdeck/pages/homepage.dart';

void main() {
  runApp(const TechDeckApp());
}

class TechDeckApp extends StatelessWidget {
  const TechDeckApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Tech Deck',
      theme: ThemeData.dark().copyWith(
        extensions: <ThemeExtension<dynamic>>[MoonTheme(
          tokens: MoonTokens.dark.copyWith(
            colors: MoonColors.dark
          )
        )],
      ),
      home: const TechDeckHomePage(),
    );
  }
}