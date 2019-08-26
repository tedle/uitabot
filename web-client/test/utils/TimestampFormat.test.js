// --- TimestampFormat.test.js -------------------------------------------------
// Test suite for TimestampFormat.js

import TimestampFormat from "utils/TimestampFormat";

const m = s => s * 60;
const h = s => s * 60 * 60;

test("negative timestamps are treated as 0", () => {
    expect(TimestampFormat(-99)).toBe("0:00");
    expect(TimestampFormat(-0.5)).toBe("0:00");
    expect(TimestampFormat(-0)).toBe("0:00");
});

test("floats are rounded", () => {
    expect(TimestampFormat(10.3)).toBe("0:10");
    expect(TimestampFormat(10.7)).toBe("0:11");
});

test("seconds are correctly formatted", () => {
    expect(TimestampFormat( 0)).toBe("0:00");
    expect(TimestampFormat( 5)).toBe("0:05");
    expect(TimestampFormat(15)).toBe("0:15");
});

test("minutes are correctly formatted", () => {
    expect(TimestampFormat(m(1) +  0)).toBe( "1:00");
    expect(TimestampFormat(m(1) + 15)).toBe( "1:15");
    expect(TimestampFormat(m(20)+  0)).toBe("20:00");
    expect(TimestampFormat(m(20)+ 15)).toBe("20:15");
});

test("hours are correctly formatted", () => {
    expect(TimestampFormat(h(1)             )).toBe(  "1:00:00");
    expect(TimestampFormat(h(1)         + 15)).toBe(  "1:00:15");
    expect(TimestampFormat(h(1) + m(15) + 15)).toBe(  "1:15:15");
    expect(TimestampFormat(h(10)            )).toBe( "10:00:00");
    expect(TimestampFormat(h(100)           )).toBe("100:00:00");
});
