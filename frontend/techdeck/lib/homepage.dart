import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';

void openNewShowDialog(BuildContext context) {
  double screenWidth = MediaQuery.of(context).size.width;
  showDialog(context: context, barrierDismissible: false, builder: (BuildContext context) {return SimpleDialog(
    title: const Text("New Show"),
    children: [
      SizedBox(width: screenWidth * 0.5),
      MoonButton(label: const Text("Create"), onTap: () {createNewShow(context); Navigator.pop(context);}, width: screenWidth*0.2)
    ],
  );});
}

void createNewShow(BuildContext context) {

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
                MoonButton(label: Text("New Show"), onTap: () {openNewShowDialog(context);}, backgroundColor: Color.fromARGB(40, 255, 255, 255), buttonSize: MoonButtonSize.xl),
                SizedBox(width: 30),
                MoonButton(label: const Text("Load Show"), onTap: () {}, backgroundColor: MoonColors.dark.piccolo, buttonSize: MoonButtonSize.xl),
            ]),
          ],
        ),
      ),
    );
  }
}