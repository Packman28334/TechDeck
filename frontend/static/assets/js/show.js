
class Show {
    constructor(title) {
        this.title = title;
        this._blackout = false;

        this.cues = [];
        this.currentCue = -1;

        this.newCueMode = false;
        this.configuringCueIndex = -1;
        this.configuringCueUuid = "";
        this.configuringCueCommands = [];

        this.newCommandMode = false;
        this.configuringCommandType = "";
        this.configuringCommandId = "";

        this.selectedCues = [];

        socket.emit("get_cues");
        socket.emit("get_current_cue");
    }

    get blackout() {
        return this._blackout;
    }

    set blackout(value) {
        socket.emit("blackout_change_state", {"action": value ? "enter": "exit"});
    }

    toggleBlackout() {
        socket.emit("blackout_change_state", {"action": "toggle"});
    }

    updateSelectedCues() {
        show.selectedCues = [];

        Array.from(getShadowDOMOf("editshow").querySelector(".cue-table").children).forEach((row) => {
            if (!row.classList.contains("header")) {
                var checkbox = row.querySelector(".select-checkbox input");
                if (checkbox?.checked) {
                    show.selectedCues.push(parseInt(checkbox.dataset.cueId));
                }
            }
        });

        if (getShadowDOMOf("editshow").querySelector(".cue-table").children.length-1 == this.selectedCues.length && this.selectedCues.length != 0) { // if all cues are selected, enable the select all checkbox
            getShadowDOMOf("editshow").querySelector(".cue-table .row.header .cell input[type=checkbox]").checked = true;
        } else { // if not all cues are selected, then disable the select all checkbox
            getShadowDOMOf("editshow").querySelector(".cue-table .row.header .cell input[type=checkbox]").checked = false;
        }

        if (show.selectedCues.length == 0) {
            getShadowDOMOf("editshow").querySelector(".toolbar").setAttribute("class", "toolbar none-selected");
        } else if (show.selectedCues.length == 1) {
            getShadowDOMOf("editshow").querySelector(".toolbar").setAttribute("class", "toolbar one-selected");
        } else {
            getShadowDOMOf("editshow").querySelector(".toolbar").setAttribute("class", "toolbar multiple-selected");
        }
    }

    addCue() {
        this.newCueMode = true;
        this.configuringCueUuid = null;
        this.configuringCueCommands = [];
        populateCueCommandList();
    }

    editCue(id) {
        this.newCueMode = false;
        this.configuringCueIndex = id;
        this.configuringCueUuid = this.cues[id]["uuid"];
        this.configuringCueCommands = this.cues[id]["commands"];
        populateCueCommandList();
        populateConfiguredCueValues();
    }

    applyCueConfiguration() {
        var description = getShadowDOMOf("editshow").getElementById("configured-cue-description").value;
        var notes = getShadowDOMOf("editshow").getElementById("configured-cue-notes").value;
        var blackout = getShadowDOMOf("editshow").getElementById("configured-cue-blackout").checked;

        var uuid = this.configuringCueUuid ? this.configuringCueUuid : window.crypto.randomUUID(); // just embracing the secure contexts atp

        if (this.newCueMode) {
            socket.emit("add_cue", {"description": description, "notes": notes, "blackout": blackout, "uuid": uuid, "commands": this.configuringCueCommands});
        } else {
            socket.emit("edit_cue", {"index": this.configuringCueIndex, "cue": {"description": description, "notes": notes, "blackout": blackout, "uuid": uuid, "commands": this.configuringCueCommands}});
        }
    }

    deleteCue(id) {
        // deselect cue before deleting because the deleteSelectedCues loop will crash under normal delay from waiting for a cue to actually be deleted
        getShadowDOMOf("editshow").querySelector(".cue-table").children[id+1].querySelector(".select-checkbox input").checked = false;
        this.updateSelectedCues();
        socket.emit("delete_cue", id);
    }

    deleteSelectedCues() {
        while(this.selectedCues.length > 0) { // we can't do for or foreach since we're changing the array with each deletion
            this.selectedCues.sort((a, b) => {a - b}).reverse(); // deletions cascade through indices, so we need to do descending order to prevent that. this also gets reset on every updateSelectedCues call, hence the loop
            this.deleteCue(this.selectedCues[0]);
        }
    }

    addCommand(commandType) {
        this.newCommandMode = true;
        this.configuringCommandType = commandType;
        populateConfigureCommandDialog(commandType);
    }

    editCommand(commandId) {
        this.newCommandMode = false;
        this.configuringCommandId = commandId;
        var command = this.configuringCueCommands.find(command => command["id"] == commandId);
        this.configuringCommandType = command["subsystem"] + "." + command["action"];
        populateConfigureCommandDialog(this.configuringCommandType);
        populateConfiguredCommandValues();
    }

    applyCommandConfiguration() {
        var commandConfiguration = Object.fromEntries(new FormData(getShadowDOMOf("editshow").getElementById("command-field-container")).entries());

        commandConfiguration["subsystem"] = this.configuringCommandType.split(".")[0];
        commandConfiguration["action"] = this.configuringCommandType.split(".")[1];
        commandConfiguration["id"] = window.crypto.randomUUID(); // i love forcing secure contexts for absolutely zero reason

        if (this.newCommandMode) {
            this.configuringCueCommands.push(commandConfiguration);
            populateCueCommandList();
            closeDialog("configure-command-dialog");
            closeDialog("add-command-dialog");
        } else {
            this.configuringCueCommands[this.configuringCueCommands.findIndex(command => command["id"] == this.configuringCommandId)] = commandConfiguration;
            populateCueCommandList();
            closeDialog("configure-command-dialog");
        }
    }

    removeCommand(commandId) {
        this.configuringCueCommands = this.configuringCueCommands.filter(command => command["id"] != commandId);
        populateCueCommandList();
    }
}

var show = undefined;

function populateCueTable() {
    if (show) {
        cueTable = getShadowDOMOf("editshow").querySelector(".cue-table");
        
        var selectedCueUuids = new Object();
        var index = 0;
        Array.from(cueTable.children).forEach(child => {
            if (!child.classList.contains("header")) {
                selectedCueUuids[child.querySelector(".cue-uuid").textContent] = child.querySelector(".select-checkbox input").checked;
                cueTable.removeChild(child);
                index++;
            }
        });

        var index = 0;
        show.cues.forEach(cue => {
            row = document.createElement("div");
            row.classList.add("row");

            if (index == show.currentCue) {
                row.classList.add("active");
            }

            row.innerHTML = `
                <div class="cell goto-button">
                    <button class="icon-button" onclick="socket.emit('jump_to_cue', $ID$);">
                        <span class="material-symbols-outlined">play_circle</span>
                    </button>
                </div>
                <div class="cell select-checkbox"><label class="checkbox"><input type="checkbox" data-cue-id="$ID$"><span></span></label></div>
                <div class="cell cue-id"><p>$DISPLAY_ID$</p></div>
                <div class="cell description"><p>$DESCRIPTION$</p></div>
                <div class="cell notes"><p>$NOTES$</p></div>
                <div class="cell edit-cue">
                        <button class="icon-button opens-dialog" onclick="show?.editCue($ID$); toggleDialog('configure-cue-dialog');">
                            <span class="material-symbols-outlined">edit</span>
                        </button>
                </div>
                <div class="cell delete-cue">
                        <button class="icon-button" onclick="show?.deleteCue($ID$);">
                            <span class="material-symbols-outlined">delete</span>
                        </button>
                </div>
                <p class="cue-uuid">$UUID$</p>
            `.replaceAll("$DESCRIPTION$", cue["description"])
            .replaceAll("$NOTES$", cue["notes"])
            .replaceAll("$ID$", index)
            .replaceAll("$DISPLAY_ID$", index+1)
            .replaceAll("$UUID$", cue["uuid"]);

            if (Object.keys(selectedCueUuids).includes(cue["uuid"]) && selectedCueUuids[cue["uuid"]]) {
                row.querySelector(".select-checkbox input").checked = true;
            }

            cueTable.appendChild(row);

            index++;
        });

        Array.from(cueTable.children).forEach((child) => {
            if (child.classList.contains("header")) {
                child.querySelector("input[type=checkbox]").addEventListener("change", (ev) => { // when we click the header's checkbox
                    Array.from(getShadowDOMOf("editshow").querySelector(".cue-table").children).forEach((row) => {
                        row.querySelector(".select-checkbox input").checked = ev.target.checked;
                    });
                    show?.updateSelectedCues();
                });
            } else {
                child.querySelector("input[type=checkbox]").addEventListener("change", (ev) => { // when we click a normal checkbox
                    show?.updateSelectedCues();
                });
            }
        });

        show?.updateSelectedCues();
    }
}

function formatCommandName(subsystem, action) {
    var subsystemName = subsystem.at(0).toUpperCase() + subsystem.slice(1, subsystem.length);

    var actionName = action.at(0).toUpperCase() + action.slice(1, action.length);

    return subsystemName + ": " + actionName.replaceAll("_", " ");
}

function formatCommandParams(command) {
    switch(command["subsystem"]) {
        case "mixer":
            switch(command["action"]) {
                case "enable_channels":
                    return command["channels"].split(" ").join(", ");
                case "disable_channels":
                    return command["channels"].split(" ").join(", ");
                case "set_faders_on_channels":
                    return command["channels"].toUpperCase().split(" ").join("dB, ").concat("dB").replaceAll("=", " = ");
                case "mute_group":
                    return command["mute_group"];
                case "unmute_group":
                    return command["mute_group"];
            }
            break;
        case "lights":
            switch(command["action"]) {
                case "jump_to_cue":
                    return command["cue"];
                case "switch_playback":
                    return "PB" + command["playback"];
            }
            break;
        case "spotlight":
            switch(command["action"]) {
                case "change_guide":
                    return '"' + command["guide"] + '"';
            }
            break;
        case "audio":
            switch(command["action"]) {
                case "play":
                    return "Track #"+command["index"];
                case "stop":
                    return "";
            }
            break;
    }
    return "";
}

function populateCueCommandList() {
    commandList = getShadowDOMOf("editshow").querySelector(".command-list");

    Array.from(commandList.children).forEach(child => {
        commandList.removeChild(child);
    });

    show.configuringCueCommands.forEach(command => {
        commandElement = document.createElement("div");
        commandElement.classList.add("command");
        commandElement.innerHTML = `
            <p>$NAME$</p>
            <p>$PARAMS$</p>
            <div>
                <button class="icon-button opens-dialog" onclick="show?.editCommand('$ID$'); openDialog('configure-command-dialog');">
                    <span class="material-symbols-outlined">edit</span>
                </button>
                <button class="icon-button opens-dialog" onclick="show?.removeCommand('$ID$');">
                    <span class="material-symbols-outlined">delete</span>
                </button>
            </div>
        `.replaceAll("$NAME$", formatCommandName(command["subsystem"], command["action"]))
        .replaceAll("$PARAMS$", formatCommandParams(command))
        .replaceAll("$ID$", command["id"]);
        commandList.appendChild(commandElement);
    });
}

function populateConfiguredCueValues() {
    var description = getShadowDOMOf("editshow").getElementById("configured-cue-description");
    var notes = getShadowDOMOf("editshow").getElementById("configured-cue-notes");
    var blackout = getShadowDOMOf("editshow").getElementById("configured-cue-blackout");

    description.value = show.cues[show.configuringCueIndex]["description"];
    notes.value = show.cues[show.configuringCueIndex]["notes"];
    blackout.checked = show.cues[show.configuringCueIndex]["blackout"];
}

function populateConfigureCommandDialog(commandType) {
    commandFieldContainer = getShadowDOMOf("editshow").getElementById("command-field-container");
    switch(commandType) {
        case "mixer.enable_channels":
            commandFieldContainer.innerHTML = `<input type="text" placeholder="Space-separated list of channels to enable" name="channels">`;
            break;
        case "mixer.disable_channels":
            commandFieldContainer.innerHTML = `<input type="text" placeholder="Space-separated list of channels to disable" name="channels">`;
            break;
        case "mixer.set_faders_on_channels":
            commandFieldContainer.innerHTML = `<input type="text" placeholder="Space-separated list of channels=desired values" name="channels">`;
            break;
        case "mixer.mute_group":
            commandFieldContainer.innerHTML = `<input type="number" placeholder="Numerical ID of mute group to mute" name="mute_group">`;
            break;
        case "mixer.unmute_group":
            commandFieldContainer.innerHTML = `<input type="number" placeholder="Numerical ID of mute group to unmute" name="mute_group">`;
            break;
        case "lights.jump_to_cue":
            commandFieldContainer.innerHTML = `<input type="number" placeholder="ID of cue to jump to" name="cue">`;
            break;
        case "lights.switch_playback":
            commandFieldContainer.innerHTML = `<input type="number" placeholder="ID of playback to switch to" name="playback">`;
            break;
        case "spotlight.change_guide":
            commandFieldContainer.innerHTML = `<input type="text" placeholder="New guide message" name="guide">`;
            break;
        case "audio.play":
            // here we go
            commandFieldContainer.innerHTML = `
                <input type="number" placeholder="Index of the desired track" name="index">
                <input type="number" placeholder="*Desired number of loops, if any (-1 for infinite)" name="loops">
                <input type="number" placeholder="*Start time (seconds)" name="start_time">
                <input type="number" placeholder="*Stop time (seconds)" name="stop_time">
                <input type="number" placeholder="*Fade in (ms)" name="fade_in">
                <input type="number" placeholder="*Fade out (ms) - only if stop time is set" name="fade_out">
            `;
            // sorry.
            break;
        case "audio.stop":
            commandFieldContainer.innerHTML = `<input type="number" placeholder="*Fade out(ms)" name="fade_out">`;
            break;
    }
}

function populateConfiguredCommandValues() {
    var commandFieldContainer = getShadowDOMOf("editshow").getElementById("command-field-container");
    var command = show.configuringCueCommands.find(command => command["id"] == show.configuringCommandId);
    switch(show.configuringCommandType) {
        case "mixer.enable_channels":
            commandFieldContainer.querySelector("input[name=channels]").value = command["channels"];
            break;
        case "mixer.disable_channels":
            commandFieldContainer.querySelector("input[name=channels]").value = command["channels"];
            break;
        case "mixer.set_faders_on_channels":
            commandFieldContainer.querySelector("input[name=channels]").value = command["channels"];
            break;
        case "mixer.mute_group":
            commandFieldContainer.querySelector("input[name=mute_group]").value = command["mute_group"];
            break;
        case "mixer.unmute_group":
            commandFieldContainer.querySelector("input[name=mute_group]").value = command["mute_group"];
            break;
        case "lights.jump_to_cue":
            commandFieldContainer.querySelector("input[name=cue]").value = command["cue"];
            break;
        case "lights.switch_playback":
            commandFieldContainer.querySelector("input[name=playback]").value = command["playback"];
            break;
        case "spotlight.change_guide":
            commandFieldContainer.querySelector("input[name=guide]").value = command["guide"];
            break;
        case "audio.play":
            commandFieldContainer.querySelector("input[name=index]").value = command["index"];
            commandFieldContainer.querySelector("input[name=loops]").value = command["loops"];
            commandFieldContainer.querySelector("input[name=start_time]").value = command["start_time"];
            commandFieldContainer.querySelector("input[name=stop_time]").value = command["stop_time"];
            commandFieldContainer.querySelector("input[name=fade_in]").value = command["fade_in"];
            commandFieldContainer.querySelector("input[name=fade_out]").value = command["fade_out"];
            break;
        case "audio.stop":
            commandFieldContainer.querySelector("input[name=fade_out]").value = command["fade_out"];
            break;
    }
}

socket.on("is_show_loaded", (state) => {
    if (state["master_node_present"]) {
        if (state["loaded"]) {
            show = new Show(state["loaded"]);
            loadPageview("editshow");
        } else {
            loadPageview("homepage");
        }
    } else {
        loadPageview("nomaster");
    }
});

socket.on("master_node", (data) => {
    if (currentPageview == "nomaster" && data["master_uuid"]) {
        loadPageview("homepage");
    }
});

socket.on("selected_show", (title) => {
    show = new Show(title);
    loadPageview("editshow");
});

socket.on("blackout_state_changed", (data) => {
    if (show) {
        show._blackout = data["new_state"];
        if (data["new_state"]) {
            getShadowDOMOf("editshow").querySelector(".main-bar > #blackout-button").classList.add("toggle-enabled");
        } else {
            getShadowDOMOf("editshow").querySelector(".main-bar > #blackout-button").classList.remove("toggle-enabled");
        }
    }
});

socket.on("cue_list_changed", (data) => {
    if (show) {
        show.cues = data["cue_list"];
        populateCueTable();
    }
});

socket.on("cue_edited", (data) => {
    if (show) {
        show.cues[data["index"]] = data["cue"];
        populateCueTable(); // TODO: re-optimize since i just unoptimized it for "cleanliness" (make it not repopulate the entire table for a single cue)
    }
});

socket.on("current_cue_changed", (index) => {
    if (show) {
        show.currentCue = index;
        populateCueTable(); // TODO: actually code properly instead of just remaking the entire table on each cue change
    }
});