
document.addEventListener("click", (ev) => {
    if (!ev.target.tagName.startsWith("TD-")) { // ignore custom elements as we can't detect dialogues there from the document
        if (!ev.target.closest(".dialog") && !ev.target.closest("button.opens-dialog")) { // if the click wasn't inside a dialog or a button which can open a dialog
            closeAllDialogs(); // close all the dialogs
        }
    }
});

document.querySelector("#pageview-container > #editshow").shadowRoot.addEventListener("click", (ev) => {
    if (!ev.target.closest(".dialog") && !ev.target.closest("button.opens-dialog")) {
        closeAllDialogs();
    }
});

function openDialog(id) {
    document.getElementById(id)?.classList.remove("closed");
    getShadowDOM().getElementById(id)?.classList.remove("closed");
}

function closeDialog(id) {
    document.getElementById(id)?.classList.add("closed");
    getShadowDOM().getElementById(id)?.classList.add("closed");
}

function toggleDialog(id) {
    if (document.getElementById(id)?.classList.contains("closed") || getShadowDOM().getElementById(id)?.classList.contains("closed")) {
        openDialog(id);
    } else {
        closeDialog(id);
    }
}

function closeAllDialogs() {
    document.querySelectorAll(".dialog").forEach((dialog, key, parent) => {
        dialog.classList.add("closed");
    });

    getShadowDOM().querySelectorAll(".dialog").forEach((dialog, key, parent) => {
        dialog.classList.add("closed");
    });
}