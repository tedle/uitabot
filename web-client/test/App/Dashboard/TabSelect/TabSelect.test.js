// --- TabSelect.test.js -------------------------------------------------------
// Test suite for TabSelect.js

import TabSelect from "components/App/Dashboard/TabSelect/TabSelect";

import React from "react";
import {render, fireEvent} from "@testing-library/react";

const tabs = [1, 2, 3, 4, 5].map(i => ({id: `id${i}`, display: `name${i}`}));

test("clicked tabs become active", () => {
    const onSelect = jest.fn();
    const {getByText} = render(<TabSelect tabs={tabs} onSelect={onSelect} active=""/>);

    for(let tab of tabs) {
        fireEvent.click(getByText(tab.display));
        expect(onSelect).toHaveBeenLastCalledWith(tab.id);
    }
});

test("default active tab", () => {
    const activeIndex = 2;
    const {getByText} = render(
        <TabSelect tabs={tabs} onSelect={jest.fn()} active={tabs[activeIndex].id}/>
    );

    tabs.forEach((tab, i) => {
        const expectedClass = i == activeIndex ? "Active" : "";
        expect(getByText(tab.display).className).toBe(expectedClass);
    });
});
