import pytest

import uita.exceptions
import uita.message


def test_ClientError():
    with pytest.raises(TypeError):
        uita.exceptions.ClientError("error message")

    error = uita.exceptions.ClientError(uita.message.AuthFailMessage())
    assert isinstance(error.message, uita.message.AuthFailMessage)
