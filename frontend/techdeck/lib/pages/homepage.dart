import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';
import 'package:techdeck/dialogs/load_show_dialog.dart';
import 'package:techdeck/dialogs/new_show_dialog.dart';
import 'package:techdeck/pages/show_page.dart';
import 'package:techdeck/backend_request_dispatcher.dart' as backend;

void openNewShowDialog(BuildContext context) {
  showDialog(context: context, builder: (BuildContext context) {return SimpleDialog(
    title: const Text("New Show"),
    children: [
      NewShowDialog()
    ],
  );});
}

void openLoadShowDialog(BuildContext context) {
  showDialog(context: context, builder: (BuildContext context) {return SimpleDialog(
    title: const Text("Load Show"),
    children: [
      LoadShowDialog()
    ],
  );});
}

Future<dynamic> getResumeShowButton(BuildContext context) async {
  Map<String, dynamic> response = await backend.get("/is_show_loaded");
  if (response['_success'] == true) {
    if (response["loaded"] == true) {
      return MoonButton(label: const Text("Resume last show"), onTap: () {
        Navigator.push(context, MaterialPageRoute(builder: ShowPage(response["show"]).build));
      });
    }
  }
  return Text("No show loaded.");
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
                MoonButton(label: const Text("Load Show"), onTap: () {openLoadShowDialog(context);}, backgroundColor: MoonColors.dark.piccolo, buttonSize: MoonButtonSize.xl),
            ]),
            SizedBox(height: 20),
            FutureBuilder(future: getResumeShowButton(context), builder: (context, snapshot) {
              if (snapshot.hasData) {
                return snapshot.data;
              } else {
                return Text("Please wait...");
              }
            })
          ],
        ),
      ),
    );
  }
}