export class AbstractMessage {
    static get header() {
        return "base";
    }

    str() {
        let obj = Object();
        obj.header = this.constructor.header;
        for(let property in this) {
            obj[property] = String(this[property]);
        }
        return JSON.stringify(obj);
    }
}

export class AuthFailMessage extends AbstractMessage {
    static get header() {
        return "auth.fail";
    }
}

export class AuthSessionMessage extends AbstractMessage {
    static get header() {
        return "auth.session";
    }

    constructor(session, user) {
        super();
        this.session = session;
        this.user = user;
    }
}

export class AuthTokenMessage extends AbstractMessage {
    static get header() {
        return "auth.token";
    }

    constructor(code) {
        super();
        this.code = code;
    }
}

const VALID_MESSAGES = {
    "auth.fail": [AuthFailMessage, []],
    "auth.session": [AuthSessionMessage, ["session","user"]],
    "auth.token": [AuthTokenMessage, ["code"]]
};

export class EventDispatcher {
    constructor() {
        this.onAuthFail = m => {}
    }

    dispatch(message) {
        if (!message instanceof AbstractMessage) {
            throw new TypeError("EventDispatcher.dispatch requires a subclass of AbstractMessage");
        }
        switch(message.constructor) {
            case AuthFailMessage:
                this.onAuthFail(message);
                break;
            default:
                throw new InternalError("EventDispatcher.dispatch has not implemented this message");
                break;
        }
    }
}

export function parse(message) {
    let obj = JSON.parse(message);
    let args = Array();
    for (let arg of VALID_MESSAGES[obj.header][1]) {
        if (arg in obj) {
            args.push(obj[arg]);
        }
        else {
            throw new TypeError("Mismatched parmeters between parsed message and associated type");
        }
    }
    // This is what modern javascript looks like
    return new (Function.prototype.bind.call(VALID_MESSAGES[obj.header][0], null, ...args));
}
