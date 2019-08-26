export default class MockWebSocket extends WebSocket {
    constructor(url) {
        // Attempt to stop the base class from modifying anything, mock the rest.
        // This is dirty but mocking a global class (and not a module) while still passing
        // react-proptype checks doesn't seem well supported by Jest itself.
        super(url);
        this.close();

        this.onopen = () => {};
        this.onerror = () => {};
        this.onmessage = () => {};
        this.onclose = () => {};

        this.send = jest.fn();
        this.close = jest.fn().mockImplementation(() => {
            this.onclose();
            this.onclose = () => {};
        });
        this._readyState = MockWebSocket.CONNECTING;

        MockWebSocket.instance = this;
    }

    get readyState() {
        return this._readyState;
    }

    set readyState(readyState) {
        this._readyState = readyState;
    }
}
