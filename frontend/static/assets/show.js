
class Show {
    constructor(title) {
        this.title = title;
    }

    toggleBlackout() {
        socket.emit("blackout_change_state", {"action": "toggle"});
    }
}