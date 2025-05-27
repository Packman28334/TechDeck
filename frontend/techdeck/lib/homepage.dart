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
            Text("Tech Deck", style: TextStyle(fontSize: 96, fontWeight: FontWeight.w900)),
            Row(mainAxisAlignment: MainAxisAlignment.center,
              children: [
                MoonButton(label: Text("New Show"), onTap: () {}, backgroundColor: MoonColors.dark.beerus),
                SizedBox(width: 30),
                MoonButton(label: Text("Load Show"), onTap: () {}, backgroundColor: MoonColors.dark.piccolo)
            ]),
          ],
        ),
      ),
    );
  }
}