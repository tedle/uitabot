// --- TouchButton.test.js -----------------------------------------------------
// Test suite for TouchButton.js

import TouchButton from "components/TouchButton/TouchButton";

import React from "react";
import {render, fireEvent} from "@testing-library/react";

const onClick = jest.fn();
const onTouchMove = jest.fn();
const onTouchEnd = jest.fn();
const onTouchCancel = jest.fn();

let button = null;

beforeEach(() => {
    const {container} = render(
        <TouchButton
            onClick={onClick}
            onTouchMove={onTouchMove}
            onTouchEnd={onTouchEnd}
            onTouchCancel={onTouchCancel}
        />
    );
    button = container.querySelector("button");
});

afterEach(() => {
    button = null;
    jest.resetAllMocks();
});

test("is tapped when no movement happens", () => {
    fireEvent.touchStart(button);
    fireEvent.touchEnd(button);
    fireEvent.click(button);

    expect(onTouchMove).not.toHaveBeenCalled();
    expect(onTouchCancel).not.toHaveBeenCalled();
    expect(onTouchEnd).toHaveBeenCalled();
    expect(onClick).toHaveBeenCalled();
    expect(onClick.mock.calls[0][0].wasTapped).toBe(true);
});

test("is not tapped when movement happens", () => {
    fireEvent.touchStart(button);
    fireEvent.touchMove(button);
    fireEvent.touchEnd(button);
    fireEvent.click(button);

    expect(onTouchMove).toHaveBeenCalled();
    expect(onTouchCancel).not.toHaveBeenCalled();
    expect(onTouchEnd).toHaveBeenCalled();
    expect(onClick).toHaveBeenCalled();
    expect(onClick.mock.calls[0][0].wasTapped).toBe(false);
});

test("is tapped when movement happens but is cancelled", () => {
    fireEvent.touchStart(button);
    fireEvent.touchMove(button);
    fireEvent.touchCancel(button);
    fireEvent.touchEnd(button);
    fireEvent.click(button);

    expect(onTouchMove).toHaveBeenCalled();
    expect(onTouchCancel).toHaveBeenCalled();
    expect(onTouchEnd).toHaveBeenCalled();
    expect(onClick).toHaveBeenCalled();
    expect(onClick.mock.calls[0][0].wasTapped).toBe(true);
});

test("does not crash when forwarding unbound events", () => {
    const {container} = render(<TouchButton/>);
    const button = container.querySelector("button");

    expect(() => fireEvent.click(button)).not.toThrow();
    expect(() => fireEvent.touchMove(button)).not.toThrow();
    expect(() => fireEvent.touchCancel(button)).not.toThrow();
    expect(() => fireEvent.touchEnd(button)).not.toThrow();
});
