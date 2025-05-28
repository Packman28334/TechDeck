import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';
import 'package:techdeck/backend_request_dispatcher.dart' as backend;
import 'package:techdeck/pages/show_page.dart';

// TODO: replace text input with dropdown

class LoadShowDialog extends StatefulWidget {
  const LoadShowDialog({super.key});

  @override
  State<LoadShowDialog> createState() => _LoadShowDialogState();
}

class _LoadShowDialogState extends State<LoadShowDialog> {

  final showNameInputController = TextEditingController();

  void loadShow(BuildContext context) {
    backend.get("/load_show/${showNameInputController.text}").whenComplete(() {
      print("Loaded show ${showNameInputController.text}");
      Navigator.pop(context);
      Navigator.push(context, MaterialPageRoute(builder: ShowPage(showNameInputController.text).build));
    });
  }

  @override
  void dispose() {
    showNameInputController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    double screenWidth = MediaQuery.of(context).size.width;

    return Column(mainAxisAlignment: MainAxisAlignment.start, children: [
      SizedBox(width: screenWidth * 0.5, height: 20),
      SingleChildScrollView(child: Column(mainAxisAlignment: MainAxisAlignment.start, children: [
        MoonTextInput(width: screenWidth*0.4, controller: showNameInputController, hintText: "Show name"),
      ])),
      SizedBox(height: 40),
      Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
        MoonButton(label: const Text("Cancel"), onTap: () {Navigator.pop(context);}, width: screenWidth*0.2),
        MoonButton(label: const Text("Load"), onTap: () {loadShow(context);}, backgroundColor: MoonColors.dark.piccolo, width: screenWidth*0.2),
      ])
    ]);
  }

}