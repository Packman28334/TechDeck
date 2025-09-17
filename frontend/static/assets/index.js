
const socket = io();
socket.emit("is_show_loaded");

var currentPageview = "homepage";
function loadPageview(pageview) {
    document.querySelector("#pageview-container > #"+currentPageview).classList.add("hidden");
    document.querySelector("#pageview-container > #"+pageview).classList.remove("hidden");
    currentPageview = pageview;
}

var show = undefined;

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
    }
});

function promoteThisNodeToMaster() {
    socket.emit("promote");
}

function selectShow() {
    socket.emit("select_show", prompt("Title: "));
}