// Reminder in case jsdom adds window.crypto support eventually
expect(window.crypto).not.toBeDefined();
// Obviously not cryptographically secure
window.crypto = {
    getRandomValues: buffer => {
        let typedBuffer = null;
        if (ArrayBuffer.isView(buffer)) {
            typedBuffer = new Uint8Array(buffer.buffer);
        }
        else {
            typedBuffer = new Uint8Array(buffer);
        }
        for (let i of typedBuffer.keys()) {
            typedBuffer[i] = Math.floor(Math.random() * 255);
        }
    }
};
