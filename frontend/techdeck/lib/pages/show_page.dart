
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
          Tooltip(message: "Begin show", child: MoonButton.icon(icon: const Icon(MoonIcons.media_play_32_regular), onTap: () {})),
          Tooltip(message: "Spotlight view", child: MoonButton.icon(icon: const Icon(MoonIcons.other_lightning_32_regular), onTap: () {})),
          Tooltip(message: "Backdrop view", child: MoonButton.icon(icon: const Icon(MoonIcons.media_video_32_regular), onTap: () {})),
          Tooltip(message: "Audio Library", child: MoonButton.icon(icon: const Icon(MoonIcons.media_music_32_regular), onTap: () {})),
          Tooltip(message: "Backdrop Library", child: MoonButton.icon(icon: const Icon(MoonIcons.generic_picture_32_regular), onTap: () {})),
          Tooltip(message: "Show configuration", child: MoonButton.icon(icon: const Icon(MoonIcons.software_settings_32_regular), onTap: () {})),
          Tooltip(message: "Home", child: MoonButton.icon(icon: const Icon(MoonIcons.generic_home_32_regular), onTap: () {Navigator.pop(context);})),
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
          Offstage(offstage: true, child: Icon(MoonIcons.time_clock_32_regular, color: MoonColors.dark.hit)),
          Offstage(offstage: !cue["blackout"], child: Icon(MoonIcons.other_moon_32_regular, color: MoonColors.dark.piccolo))
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
        Row(mainAxisAlignment: MainAxisAlignment.center, spacing: 10, children: () {
          if (selectedCues.isEmpty) {
            return <Widget>[  
              Tooltip(message: "Create cue", child: MoonButton.icon(icon: const Icon(MoonIcons.files_add_text_32_regular), onTap: () {})),
            ];
          } else if (selectedCues.length == 1) {
            return <Widget>[
              Tooltip(message: "Insert cue after", child: MoonButton.icon(icon: const Icon(MoonIcons.files_add_text_32_regular), onTap: () {})),
              Tooltip(message: "Edit cue", child: MoonButton.icon(icon: const Icon(MoonIcons.generic_edit_32_regular), onTap: () {})),
              Tooltip(message: "Raise cue", child: MoonButton.icon(icon: const Icon(MoonIcons.arrows_up_32_regular), onTap: () {})),
              Tooltip(message: "Lower cue", child: MoonButton.icon(icon: const Icon(MoonIcons.arrows_down_32_regular), onTap: () {})),
              Tooltip(message: "Jump to cue", child: MoonButton.icon(icon: const Icon(MoonIcons.media_play_32_regular), onTap: () {})),
              Tooltip(message: "Delete cue", child: MoonButton.icon(icon: const Icon(MoonIcons.files_delete_32_regular), onTap: () {})),
            ];
          } else {
            return <Widget>[
              MoonButton.icon(icon: const Icon(null)) // for spacing
            ];
          }
        }()),
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