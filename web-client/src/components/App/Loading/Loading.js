// --- Loading.js --------------------------------------------------------------
// Loading transition display component

import "./Loading.scss";

import React from "react";
import PropTypes from "prop-types";

export default function Loading({children}) {
    return (
        <div className="Loading">
            {children} <i className="fas fa-spinner fa-spin"></i>
        </div>
    );
}

Loading.propTypes = {
    children: PropTypes.node.isRequired
};
