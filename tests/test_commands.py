import argparse
from unittest.mock import Mock, create_autospec
from cliqq import commands


def test_dispatch_with_args():
    # learned from test all funcs called by dispatch REQUIRE keywrd args

    # * ensures all after are passed by keyword
    def fake_func(*, args, api_config, registry):
        return True

    # create a mock w attributes of fake_func
    # side_effect = Mock kywrd arg meaning it calls that whenever it's invoked
    # rather than just recording calls
    func = create_autospec(fake_func, side_effect=fake_func)
    # mocks don't expose the wrapped func's signature, above does
    # func = Mock(wraps=fake_func)

    api_config = Mock()

    registry = Mock()
    # creating a fake Command with info
    registry.commands = {"/test": Mock()}
    registry.commands["/test"].function = func
    registry.commands["/test"].description = "this is fake!"
    registry.commands["/test"].args = "[argument]"

    # cli input
    user_input = argparse.Namespace(command="/test", args=["argument"], prompt=[])

    commands.dispatch(
        user_input=user_input,
        api_config=api_config,
        history=Mock(),
        registry=registry,
        paths=Mock(),
    )

    print(func.call_args)

    # Assert func was called once with the right kwargs
    func.assert_called_once_with(
        args="argument",
        api_config=api_config,
        registry=registry,
    )
