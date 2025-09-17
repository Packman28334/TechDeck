
class Show {
    constructor(title) {
        this.title = title;
        this._blackout = false;
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
}