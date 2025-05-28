import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';
import 'package:techdeck/backend_request_dispatcher.dart' as backend;

class NewShowDialog extends StatefulWidget {
  const NewShowDialog({super.key});

  @override
  State<NewShowDialog> createState() => _NewShowDialogState();
}

class _NewShowDialogState extends State<NewShowDialog> {

  final showNameInputController = TextEditingController();

  void createNewShow(BuildContext context) {
    backend.get("/new_show/${showNameInputController.text}");
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
        MoonButton(label: const Text("Create"), onTap: () {createNewShow(context); Navigator.pop(context);}, backgroundColor: MoonColors.dark.piccolo, width: screenWidth*0.2),
      ])
    ]);
  }

}