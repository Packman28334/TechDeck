
import 'package:flutter/material.dart';
import 'package:moon_design/moon_design.dart';
import 'package:techdeck/backend_request_dispatcher.dart' as backend;

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

  List<int> selectedCues = [];

  Future<List<MoonTableRow>> _getCueList() async {
    Map<String, dynamic> response = await backend.get("/list_cues");
    if (response["_success"] == true) {
      List<MoonTableRow> out = [];
      int i = -1;
      for (Map<String, dynamic> cue in response["cues"]) {
        i++;
        final int index = i;
        out.add(MoonTableRow(cells: [
          MoonCheckbox(value: selectedCues.contains(index), onChanged: (newValue) {
            if (selectedCues.contains(index)) {
              setState(() {selectedCues.remove(index);});
            } else {
              setState(() {selectedCues.add(index);});
            }
          }),
          Text(index.toString()),
          Text(cue["description"]),
          Offstage(offstage: true, child: const Icon(MoonIcons.time_clock_32_regular)),
          Offstage(offstage: !cue["blackout"], child: const Icon(MoonIcons.other_moon_32_regular))
        ]));
      }
      return out;
    } else {
      return [];
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      return Column(mainAxisAlignment: MainAxisAlignment.start, children: [
        SizedBox(height: 10),
        Row(mainAxisAlignment: MainAxisAlignment.center, spacing: 10, children: [
          MoonButton.icon(icon: const Icon(MoonIcons.files_add_text_32_regular), onTap: () {}),
        ]),
        SizedBox(height: 10),
        FutureBuilder(future: _getCueList(), builder: (context, snapshot) {
          if (snapshot.hasData) {
            return MoonTable(
              columnsCount: 5,
              rowSize: MoonTableRowSize.md,
              sortColumnIndex: 1,
              height: constraints.maxHeight * 0.8,
              scrollBehaviour: ScrollBehavior().copyWith(scrollbars: true),
              header: MoonTableHeader(columns: [
                MoonTableColumn(cell: const Text(""), showSortingIcon: false, width: 40), // checkbox
                MoonTableColumn(cell: const Text("ID"), showSortingIcon: false, width: 50), // id
                MoonTableColumn(cell: const Text("Description"), showSortingIcon: false, width: constraints.maxWidth*0.8-170), // description
                MoonTableColumn(cell: const Text(""), showSortingIcon: false, width: 40), // timed icon
                MoonTableColumn(cell: const Text(""), showSortingIcon: false, width: 40), // blackout icon
              ]),
              rows: snapshot.data!,
            );
          } else {
            return Text("Loading cues...");
          }
        })
      ]);
    });
  }
}