from mathics.session import MathicsSession

session = MathicsSession(add_builtin=True, catch_interrupt=False)

def check_evaluation(str_expr: str, str_expected: str, message=""):
    """Helper function to test that a WL expression against
    its results"""
    result = session.evaluate(str_expr)
    print("XXX", result)
    expected = session.evaluate(str_expected)
    print("YYY", expected)

    if message:
        assert result == expected, "%s: got: %s" % (message, result)
    else:
        assert result == expected
