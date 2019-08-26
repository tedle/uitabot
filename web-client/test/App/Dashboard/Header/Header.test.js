// --- Header.test.js ----------------------------------------------------------
// Test suite for Header.js

import Header from "components/App/Dashboard/Header/Header";

import React from "react";
import {render} from "@testing-library/react";

test("displays user and server info", () => {
    const server = {name: "Server Name"};
    const user = {avatar: "http://example.com/image.png", name: "User Name"};

    const {container, getByText} = render(<Header discordServer={server} discordUser={user}/>);
    const img = container.querySelector("img");

    expect(getByText(server.name)).toBeDefined();
    expect(getByText(user.name)).toBeDefined();
    expect(img).not.toBeNull();
    expect(img.src).toBe(user.avatar);
});
