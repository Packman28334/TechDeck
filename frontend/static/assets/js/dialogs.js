
document.querySelector("#pageview-container > #editshow").shadowRoot.addEventListener("click", (ev) => {
    if (!ev.target.closest(".dialog") && !ev.target.closest("button.opens-dialog")) {
        closeAllDialogs();
    }
});

function openDialog(id) {
    getShadowDOM().getElementById(id)?.classList.remove("closed");
}

function openDialogInPageview(pageview, id) {
    getShadowDOMOf(pageview).getElementById(id)?.classList.remove("closed");
}

function closeDialog(id) {
    getShadowDOM().getElementById(id)?.classList.add("closed");
    resetInputsOfChildren(getShadowDOM().getElementById(id));
}

function closeDialogInPageview(pageview, id) {
    getShadowDOMOf(pageview).getElementById(id)?.classList.add("closed");
    resetInputsOfChildren(getShadowDOMOf(pageview).getElementById(id));
}

function toggleDialog(id) {
    if (getShadowDOM().getElementById(id)?.classList.contains("closed")) {
        openDialog(id);
    } else {
        closeDialog(id);
    }
}

function toggleDialogInPageview(pageview, id) {
    if (getShadowDOMOf(pageview).getElementById(id)?.classList.contains("closed")) {
        openDialogInPageview(pageview, id);
    } else {
        closeDialogInPageview(pageview, id);
    }
}

function closeAllDialogs() {
    getShadowDOM().querySelectorAll(".dialog").forEach((dialog, key, parent) => {
        dialog.classList.add("closed");
        resetInputsOfChildren(dialog);
    });
}