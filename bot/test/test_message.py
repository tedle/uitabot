import pytest

import uita.message


def test_parse():
    # Exceeds max length
    with pytest.raises(uita.exceptions.MalformedMessage):
        message = '{"header":"' + '.' * uita.message.MAX_CLIENT_MESSAGE_LENGTH + '"}'
        uita.message.parse(message)
    # Mangled JSON
    with pytest.raises(uita.exceptions.MalformedMessage):
        message = '{"header"/: ''}'
        uita.message.parse(message)
    # Missing header
    with pytest.raises(uita.exceptions.MalformedMessage):
        message = '{"property": 0}'
        uita.message.parse(message)
    # Exceeds max header length
    with pytest.raises(uita.exceptions.MalformedMessage):
        message = '{"header":"' + '.' * (uita.message.MAX_HEADER_LENGTH + 1) + '"}'
        uita.message.parse(message)
    # Header does not exist
    with pytest.raises(uita.exceptions.MalformedMessage):
        message = '{"header":"bad.header"}'
        uita.message.parse(message)
    # Missing required property
    with pytest.raises(uita.exceptions.MalformedMessage):
        message = '{"header":"auth.code"}'
        uita.message.parse(message)
    # Finally success
    code = "goodcode"
    message = '{"header":"auth.code", "code":"' + code + '"}'
    parsed_message = uita.message.parse(message)
    assert isinstance(parsed_message, uita.message.AuthCodeMessage)
    assert parsed_message.code == code
