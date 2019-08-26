// --- Login.test.js -----------------------------------------------------------
// Test suite for Login.js

import Login from "components/App/Login/Login";

import React from "react";
import {render} from "@testing-library/react";

test("login button uses given URL", () => {
    const url = "http://example.com/";
    const {container} = render(<Login url={url}/>);
    expect(container.querySelector(`a[href="${url}"]`)).not.toBeNull();
});
