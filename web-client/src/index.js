// --- index.js ----------------------------------------------------------------
// Injects App component into document root

import React from "react";
import ReactDOM from "react-dom";
import App from "./components/App/App";

ReactDOM.render(<App/>, document.getElementById("App-Mount"));
