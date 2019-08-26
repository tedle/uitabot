// --- RandomString.test.js ----------------------------------------------------
// Test suite for RandomString.js

import RandomString from "utils/RandomString";

test("random strings are sized properly", () => {
    const keys = [...Array(100).keys()];
    const lengths = keys.map(i => RandomString(i).length);
    expect(lengths).toEqual(keys);
});

test("random strings are random", () => {
    const strings = new Array(100).fill(0).map(() => RandomString(100));
    const uniqueStrings = new Set(strings);
    expect(strings.length).toBe(uniqueStrings.size);
});
