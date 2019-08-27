// --- Errors.js ---------------------------------------------------------------
// Components for displaying fatal errors or a list of error-related popups

import "./Errors.scss";

import React from "react";
import PropTypes from "prop-types";
import {CSSTransition, TransitionGroup} from "react-transition-group";

const Context = React.createContext(() => {});
export {Context};

export function Fatal({children}) {
    return (
        <div className="Errors">
            <i className="fas fa-times"></i> {children}
        </div>
    );
}

export class List extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
        };
    }

    render() {
        const errors = this.props.errors.map(error => {
            return (
                <CSSTransition
                    key={error.id}
                    timeout={300}
                    classNames="Errors-List-Item"
                >
                    <li key={error.id} className="Errors-List-Item">
                        <div className="Errors-Message">
                            {error.message}
                        </div>
                        <button onClick={() => this.props.onRemove(error.id)}>
                            <i className="fas fa-times"></i>
                        </button>
                    </li>
                </CSSTransition>
            );
        });
        return (
            <div className="Errors-List">
                <TransitionGroup component={"ul"}>
                    {errors}
                </TransitionGroup>
            </div>
        );
    }
}

Fatal.propTypes = {
    children: PropTypes.node.isRequired
};

List.propTypes = {
    errors: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string,
        message: PropTypes.string
    })).isRequired,
    onRemove: PropTypes.func.isRequired
};
