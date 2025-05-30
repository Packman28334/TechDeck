
import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';

class ShowPage extends StatefulWidget {
  final String showName;

  const ShowPage(this.showName, {super.key});

  @override
  State<ShowPage> createState() => _ShowPageState();
}

class _ShowPageState extends State<ShowPage> {
  int selectedNavbarPageIndex = 0;

  Widget selectedNavbarPage() {
    switch (selectedNavbarPageIndex) {
      case 0:
        return CuesList();
      default:
        return Placeholder();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.showName),
        automaticallyImplyLeading: false,
        actions: [
          MoonButton.icon(icon: const Icon(MoonIcons.generic_home_32_regular), onTap: () {Navigator.pop(context);},),
          SizedBox(width: 10,)
        ],
      ),
      body: Row(children: [
        NavigationRail(
          destinations: [
            NavigationRailDestination(icon: const Icon(Icons.edit), label: const Text("Edit Cues")),
            NavigationRailDestination(icon: const Icon(Icons.settings), label: const Text("Show Settings")),
          ],
          selectedIndex: selectedNavbarPageIndex,
          extended: false,
          onDestinationSelected: (index) {setState(() {selectedNavbarPageIndex = index;});},
        ),
        Expanded(child: selectedNavbarPage()),
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