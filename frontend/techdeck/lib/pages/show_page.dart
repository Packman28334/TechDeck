
import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';

class ShowPage extends StatelessWidget {
  final String showName;

  const ShowPage(this.showName, {super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(showName),
        automaticallyImplyLeading: false,
        actions: [
          MoonButton.icon(icon: const Icon(MoonIcons.generic_home_32_regular), onTap: () {Navigator.pop(context);},),
          SizedBox(width: 10,)
        ],
      ),
      body: Row(children: [
        Expanded(child: CuesList()),
      ],),
    );
  }
}

class CuesList extends StatelessWidget {
  const CuesList({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView();
  }
}