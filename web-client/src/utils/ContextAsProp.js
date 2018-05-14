// --- ContextAsProp.js ----------------------------------------------------------
// Utility component for converting React context values into props

import React from "react";

export default function ContextAsProp(Component, Context, propName) {
    return function WrappedComponent(props) {
        return (
            <Context.Consumer>
                {value => {
                    const valueProp = {[propName]: value};
                    return <Component {...props} {...valueProp}/>;
                }}
            </Context.Consumer>
        );
    };
}
