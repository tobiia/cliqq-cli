import argparse
from unittest.mock import Mock
from cliqq import commands


def test_dispatch_with_args():

    def fake_func(api_config, registry, args):
        return True

    func = Mock(wraps=fake_func)

    api_config = Mock()

    registry = Mock()
    # creating a fake Command with info
    registry.commands = {"/test": Mock()}
    registry.commands["/test"].function = func
    registry.commands["/test"].description = "this is fake!"
    registry.commands["/test"].args = True

    # cli input
    user_input = argparse.Namespace(command="/test", args=["argument"], prompt=[])

    commands.dispatch(api_config, Mock(), registry, Mock(), user_input)

    # Assert func was called once with the right kwargs
    func.assert_called_once_with(
        api_config=api_config,
        registry=registry,
        args=["argument"],
    )
