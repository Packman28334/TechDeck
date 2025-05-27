import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';

class TechDeckHomePage extends StatelessWidget {
  const TechDeckHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color.fromARGB(255, 18, 18, 18),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text("Tech Deck", style: TextStyle(fontSize: 96, fontWeight: FontWeight.w900)),
            SizedBox(height: 80),
            Row(mainAxisAlignment: MainAxisAlignment.center,
              children: [
                MoonButton(label: Text("New Show"), onTap: () {}, backgroundColor: Color.fromARGB(40, 255, 255, 255), buttonSize: MoonButtonSize.xl),
                SizedBox(width: 30),
                MoonButton(label: const Text("Load Show"), onTap: () {}, backgroundColor: MoonColors.dark.piccolo, buttonSize: MoonButtonSize.xl)
            ]),
          ],
        ),
      ),
    );
  }
}