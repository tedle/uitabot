// --- Loading.test.js ---------------------------------------------------------
// Test suite for Loading.js

import Loading from "components/App/Loading/Loading";

import React from "react";
import {render} from "@testing-library/react";

test("should have inner text", () => {
    const {getByText} = render(<Loading>Hello</Loading>);
    expect(getByText(/Hello/)).toBeDefined();
});
