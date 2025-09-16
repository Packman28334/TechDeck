const socket = io();

Array.from(document.getElementsByClassName("page-view-component")).forEach(element => {
    element.shadowRoot.socket = socket;
});