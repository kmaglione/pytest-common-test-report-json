import json
from pytest import Pytester, fixture

from .conftest import PartialDict

pytest_plugins = ["pytester", "xdist", "ctrf"]
test_file = "test_example.py"
basic_test_args = ["--import-mode=importlib", "-k", "test_example"]


def run_pytest(pytester: Pytester, *args: str):
    pytester.copy_example(test_file)
    pytester.runpytest(*basic_test_args, "--ctrf", "report.json", *args)
    with open(pytester.path / "report.json") as file:
        return json.load(file)


@fixture
def ctrf_report_sync(pytester: Pytester):
    yield run_pytest(pytester)


@fixture
def ctrf_report_xdist(pytester: Pytester):
    yield run_pytest(pytester, "-n", "3")


def test_without_plugin_no_xdist(pytester: Pytester):
    pytester.copy_example(test_file)
    result = pytester.runpytest(*basic_test_args)
    result.assert_outcomes(passed=16, skipped=1, failed=3, errors=2)


def test_without_plugin_with_xdist(pytester: Pytester):
    pytester.copy_example(test_file)
    result = pytester.runpytest(*[*basic_test_args, "-n", "3"])
    result.assert_outcomes(passed=16, skipped=1, failed=3, errors=2)
    assert "created: 3/3 workers" in result.stdout.str()


def test_with_markers(pytester: Pytester):
    pytester.copy_example(test_file)
    args = [*basic_test_args, "--ctrf", "report.json", "-m smoke"]
    pytester.runpytest(*args)
    with open(pytester.path / "report.json") as file:
        report = json.load(file)
    assert report["results"]["summary"] >= PartialDict({
        "tests": 1,
        "passed": 1,
        "failed": 0,
        "skipped": 0,
    })


def test_with_plugin_no_xdist(ctrf_report_sync):
    assert ctrf_report_sync["results"]["summary"] >= PartialDict({
        "tests": 13,
        "passed": 7,
        "failed": 5,
        "skipped": 1,
    })


def test_with_plugin_failed_details(ctrf_report_sync):
    for test in ctrf_report_sync["results"]["tests"]:
        if test["status"] == "failed" and test.get("rawStatus") == "call_failed":
            assert isinstance(test.get('trace'), str)
            assert isinstance(test.get("message"), str)


def test_any_test_has_timestamps(ctrf_report_sync):
    for test in ctrf_report_sync["results"]["tests"]:
        assert isinstance(test.get("start"), int)
        assert isinstance(test.get("stop"), int)
        assert isinstance(test.get("duration"), int)


def test_with_plugin_with_xdist(ctrf_report_xdist):
    assert ctrf_report_xdist["results"]["summary"] >= PartialDict({
        "tests": 13,
        "passed": 7,
        "failed": 5,
        "skipped": 1,
    })


def test_with_plugin_failed_details_xdist(ctrf_report_xdist):
    for test in ctrf_report_xdist["results"]["tests"]:
        if test["status"] == "failed" and test.get("rawStatus") == "call_failed":
            assert isinstance(test.get('trace'), str)
            assert isinstance(test.get("message"), str)


def test_any_test_has_timestamps_xdist(ctrf_report_xdist):
    for test in ctrf_report_xdist["results"]["tests"]:
        assert isinstance(test.get("start"), int)
        assert isinstance(test.get("stop"), int)
        assert isinstance(test.get("duration"), int)
        if test["name"] == "test_with_ctrf_suite_mark":
            assert test.get("suite") == ["suite_name"]
        else:
            assert test.get("suite") == ["test_example.py"]


def test_ctrf_suite_option(pytester: Pytester):
    report = run_pytest(pytester, "--ctrf-suite=custom_suite")

    for test in report["results"]["tests"]:
        if test["name"] == "test_with_ctrf_suite_mark":
            assert test.get("suite") == ["suite_name"]
        else:
            assert test.get("suite") == ["custom_suite", "test_example.py"]
