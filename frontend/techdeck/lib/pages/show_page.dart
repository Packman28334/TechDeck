
import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';

class ShowPage extends StatelessWidget {
  const ShowPage(this.showName, {super.key});

  final String showName;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color.fromARGB(255, 18, 18, 18),
      appBar: AppBar(
        title: Text(showName),
        automaticallyImplyLeading: false,
        backgroundColor: Color.fromARGB(255, 0, 0, 0),
        actions: [
          MoonButton.icon(icon: const Icon(MoonIcons.generic_home_32_regular), onTap: () {Navigator.pop(context);},),
          SizedBox(width: 10,)
        ],
      ),
      body: CuesList()
    );
  }
}

class CuesList extends StatefulWidget {
  CuesList({super.key});

  @override
  State<CuesList> createState() => _CuesListState();
}

class _CuesListState extends State<CuesList> {
  _CuesListState();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      return Column(mainAxisAlignment: MainAxisAlignment.start, children: [
        SizedBox(height: 10),
        Row(mainAxisAlignment: MainAxisAlignment.center, spacing: 10, children: [
          MoonButton.icon(icon: const Icon(MoonIcons.files_add_text_32_regular), onTap: () {}),
        ]),
        SizedBox(height: 10),
        MoonTable(
          columnsCount: 4,
          rowSize: MoonTableRowSize.sm,
          tablePadding: EdgeInsets.symmetric(horizontal: 16),
          sortColumnIndex: 1,
          width: constraints.maxWidth,
          height: constraints.maxHeight,
          header: MoonTableHeader(columns: [
            MoonTableColumn(cell: const Text(""), showSortingIcon: false),
            MoonTableColumn(cell: const Text("ID"), showSortingIcon: false),
            MoonTableColumn(cell: const Text("Description"), showSortingIcon: false),
            MoonTableColumn(cell: const Text(""), showSortingIcon: false),
          ]),
          rows: [ // columns: jump, id, description, edit
            MoonTableRow(cells: [const Text("Hello, World!"), const Text("Hello, World!"), const Text("Hello, World!"), const Text("Hello, World!")])
          ]
        )
      ]);
    });
  }
}