import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';
import 'package:techdeck/new_show_dialog.dart';

void openNewShowDialog(BuildContext context) {
  showDialog(context: context, builder: (BuildContext context) {return SimpleDialog(
    title: const Text("New Show"),
    children: [
      NewShowDialog()
    ],
  );});
}

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
                MoonButton(label: Text("New Show"), onTap: () {openNewShowDialog(context);}, backgroundColor: Color.fromARGB(25, 255, 255, 255), buttonSize: MoonButtonSize.xl),
                SizedBox(width: 30),
                MoonButton(label: const Text("Load Show"), onTap: () {}, backgroundColor: MoonColors.dark.piccolo, buttonSize: MoonButtonSize.xl),
            ]),
          ],
        ),
      ),
    );
  }
}