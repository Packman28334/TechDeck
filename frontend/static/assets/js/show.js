
class Show {
    constructor(title) {
        this.title = title;
        this._blackout = false;

        this.newCueMode = false;
        this.configuringCueIndex = -1;
        this.configuringCueCommands = [];

        this.newCommandMode = false;
        this.configuringCommandType = "";
        this.configuringCommandId = "";

        socket.emit("get_cues");
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

    addCue() {
        this.newCueMode = true;
    }

    editCue() {
        this.newCueMode = false;
    }

    applyCueConfiguration() {
        var description = getShadowDOM().getElementById("configured-cue-description").value;
        var notes = getShadowDOM().getElementById("configured-cue-notes").value;

        if (this.newCueMode) {
            socket.emit("add_cue", {"description": description, "notes": notes, "blackout": false, "commands": this.configuringCueCommands});
        } else {

        }
    }

    addCommand(commandType) {
        this.newCommandMode = true;
        this.configuringCommandType = commandType;
        populateConfigureCommandDialog(commandType);
    }

    editCommand() {
        this.newCommandMode = false;
    }

    applyCommandConfiguration() {
        var commandConfiguration = Object.fromEntries(new FormData(getShadowDOM().getElementById("command-field-container")).entries());

        commandConfiguration["subsystem"] = this.configuringCommandType.split(".")[0];
        commandConfiguration["action"] = this.configuringCommandType.split(".")[1];
        commandConfiguration["id"] = window.crypto.randomUUID();

        if (this.newCommandMode) {
            this.configuringCueCommands.push(commandConfiguration);
            closeDialog("configure-command-dialog");
            closeDialog("add-command-dialog");
        } else {
            this.configuringCueCommands.find((command) => {command["id"] == this.configuringCommandId})[0] = commandConfiguration;
            closeDialog("configure-command-dialog");
        }
    }
}

var show = undefined;

function populateConfigureCommandDialog(commandType) {
    commandFieldContainer = getShadowDOM().getElementById("command-field-container");
    switch(commandType) {
        case "mixer.enable_channels":
            commandFieldContainer.innerHTML = `<input type="text" placeholder="Space-separated list of channels to enable" name="channels">`;
            break;
        case "mixer.disable_channels":
            commandFieldContainer.innerHTML = `<input type="text" placeholder="Space-separated list of channels to disable" name="channels">`;
            break;
    }
}

function populateCueCommandList() {

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
        cueTable = getShadowDOMOf("editshow").querySelector(".cue-table");
        
        Array.from(cueTable.children).forEach(child => {
            if (!child.classList.contains("header")) {
                cueTable.removeChild(child);
            }
        });

        var index = 0;
        data["cue_list"].forEach(cue => {
            index++;

            row = document.createElement("div");
            row.classList.add("row");

            row.innerHTML = `
                <div class="cell goto-button">
                    <button class="icon-button" onclick="socket.emit('jump_to_cue', $ID$);">
                        <span class="material-symbols-outlined">play_circle</span>
                    </button>
                </div>
                <div class="cell select-checkbox"><input type="checkbox"></div>
                <div class="cell cue-id"><p>$ID$</p></div>
                <div class="cell description"><p>$DESCRIPTION$</p></div>
                <div class="cell notes"><p>$NOTES$</p></div>
                <div class="cell edit-button">
                    <button class="icon-button opens-dialog" onclick="show?.editCue(); toggleDialog('configure-cue-dialog');">
                        <span class="material-symbols-outlined">edit</span>
                    </button>
                </div>
            `.replaceAll("$DESCRIPTION$", cue["description"])
            .replaceAll("$NOTES$", cue["notes"])
            .replaceAll("$ID$", index);

            cueTable.appendChild(row);
        });
    }
});