
const socket = io();
socket.emit("is_show_loaded");
socket.emit("client_ping", new Date().getTime());

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

function getShadowDOMOf(pageview) {
    return document.querySelector("#pageview-container > #"+pageview).shadowRoot;
}

socket.on("client_ping", (timestamp) => {
    getShadowDOMOf("editshow").getElementById("client-ping").textContent = "Ping to host: "+(new Date().getTime()-timestamp).toString()+"ms";
    setTimeout(() => {
        socket.emit("client_ping", new Date().getTime());
    }, 1000);
});

function selectShow() {
    socket.emit("select_show", prompt("Title: "));
}