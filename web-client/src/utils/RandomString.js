// --- RandomString.js ---------------------------------------------------------
// Generate a cryptographically secure random string

export default function(length) {
    // Each byte is encoded as 2 characters, so half length
    let byteArray = new Uint8Array(Math.ceil(length / 2));
    window.crypto.getRandomValues(byteArray);
    return byteArray
        // Byte for byte, converts array into a hex string
        .reduce((str, byte) => str + byte.toString(16).padStart(2, "0"), "")
        // Odd lengths produce an extra character because they are generated in pairs
        .slice(0, length);
}
