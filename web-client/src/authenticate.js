import * as QueryString from "query-string";

export default function authenticate(socket) {
    const query = QueryString.parse(location.search);
    if ('code' in query) {
        socket.send(`{"header":"auth.token","code":"${code}"}`);
    }
    socket.send('{"header":"auth.session","user":"me","session":"12345"}');
}
