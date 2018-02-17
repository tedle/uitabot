const VALID_MESSAGES = {
    "auth.fail": [AuthFailMessage, ["session","user"]],
    "auth.session": [AuthSessionMessage, ["session","user"]],
    "auth.token": [AuthTokenMessage, ["code"]]
};

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
    // (it's constructing a class from an array of arguments)
    return new (Function.prototype.bind.apply(VALID_MESSAGES[obj.header][0], [null].concat(args)));
}
