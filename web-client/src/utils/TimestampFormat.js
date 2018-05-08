// --- TimestampFormat.js ------------------------------------------------------
// Formats timestamps into displayable strings

// Formats seconds as 1:03:00, 6:14, 0:05, etc
export default function(seconds) {
    let display = "";
    if (seconds > 60 * 60) {
        display += `${Math.floor(seconds / (60 * 60))}:`;
        display += `${Math.floor(seconds / 60) % 60}:`.padStart(3, "0");
    } else {
        display += `${Math.floor(seconds / 60) % 60}:`;
    }
    display += `${seconds % 60}`.padStart(2, "0");
    return display;
}
