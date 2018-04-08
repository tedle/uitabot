// --- RandomString.js ---------------------------------------------------------
// Generate a cryptographically secure random string

export default function(length) {
    // Each byte is encoded as 2 characters, so half length
    let byteArray = new Uint8Array(length / 2);
    window.crypto.getRandomValues(byteArray);
    let str = String();
    // Byte for byte, converts array into a hex string
    for (let byte of byteArray) {
        str += byte.toString(16);
    }
    return str;
}
