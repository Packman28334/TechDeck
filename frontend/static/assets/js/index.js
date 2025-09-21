
const socket = io();
socket.emit("is_show_loaded");

var currentPageview = "homepage";
function loadPageview(pageview) {
    document.querySelector("#pageview-container > #"+currentPageview).classList.add("hidden");
    document.querySelector("#pageview-container > #"+pageview).classList.remove("hidden");

    closeAllDialogs(); // close all dialogs on the current pageview before changing to the new one

    currentPageview = pageview;

    switch(pageview) {
        case "editshow":
            getShadowDOM().querySelector(".main-bar > #title").textContent = show.title;
            break;
        default:
            break;
    }
}

function getShadowDOM() {
    return document.querySelector("#pageview-container > #"+currentPageview).shadowRoot;
}

function promoteThisNodeToMaster() {
    socket.emit("promote");
}

function selectShow() {
    socket.emit("select_show", prompt("Title: "));
}