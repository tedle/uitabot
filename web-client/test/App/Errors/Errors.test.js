// --- Errors.test.js ----------------------------------------------------------
// Test suite for Errors.js

import * as Errors from "components/App/Errors/Errors";

import React from "react";
import {render, fireEvent, waitForElementToBeRemoved} from "@testing-library/react";

test("fatal errors should render children", () => {
    const text = "Test Text";
    const {getByText} = render(<Errors.Fatal><div>{text}</div></Errors.Fatal>);
    expect(getByText(text)).toBeDefined();
});

test("error list remove button should trigger onRemove", () => {
    const errors = ["1", "2", "3"].map(i => ({id: i, message: `Error ${i}`}));
    const onRemove = jest.fn();
    const {container} = render(<Errors.List errors={errors} onRemove={onRemove}/>);

    const buttons = container.querySelectorAll("button");
    for (let button of buttons) {
        fireEvent.click(button);
    }
    for (let error of errors) {
        expect(onRemove).toHaveBeenCalledWith(error.id);
    }
});

test("error list updates when items removed", async () => {
    const errors = ["1", "2", "3"].map(i => ({id: i, message: `Error ${i}`}));

    const {container, rerender} = render(<Errors.List errors={errors} onRemove={jest.fn()}/>);
    expect(container.querySelectorAll("li").length).toBe(errors.length);

    rerender(<Errors.List errors={[]} onRemove={jest.fn()}/>);
    await waitForElementToBeRemoved(() => container.querySelector("li"));
});
