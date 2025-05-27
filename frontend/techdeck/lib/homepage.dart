import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';

class TechDeckHomePage extends StatelessWidget {
  const TechDeckHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            MoonButton(label: Text("Hello, World!"), onTap: () {print("plz work");},)
          ],
        ),
      ),
    );
  }
}