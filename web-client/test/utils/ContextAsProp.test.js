// --- ContextAsProp.test.js ---------------------------------------------------
// Test suite for ContextAsProp.js

import ContextAsProp from "utils/ContextAsProp";

import React from "react";
import PropTypes from "prop-types";
import {render, fireEvent} from "@testing-library/react";

test("forwards context as prop", () => {
    const Context = React.createContext(() => {});
    const Component = props => (<button onClick={props.contextValue}/>);
    Component.propTypes = {contextValue: PropTypes.func.isRequired};
    const WrappedComponent = ContextAsProp(Component, Context, "contextValue");
    const callback = jest.fn();

    const {container} = render(
        <Context.Provider value={callback}>
            <WrappedComponent/>
        </Context.Provider>
    );

    expect(callback).not.toHaveBeenCalled();
    fireEvent.click(container.querySelector("button"));
    expect(callback).toHaveBeenCalled();
});
