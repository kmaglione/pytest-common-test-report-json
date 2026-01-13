from pytest import Config, Parser, FixtureRequest, fixture
from ctrf.CommonTestReportPlugin import CTRF
from ctrf.BaseMetadataReport import BaseMetadataReport


def pytest_addoption(parser: Parser):
    group = parser.getgroup('ctrf', 'generate test report in CTR format')
    group.addoption('--ctrf',
                    action='store',
                    help='generate test report. Report file name is optional')
    group.addoption('--ctrf-suite',
                    action='store',
                    default='pytest',
                    help='Suite name to use in CTRF report')


def pytest_configure(config: Config):
    config.addinivalue_line(
        "markers", "ctrf_suite(name): set the CTRF suite name for use in the test report"
    )

    if not config.option.ctrf:
        return
    if hasattr(config, 'workerinput'):
        plugin = BaseMetadataReport(config)
    else:
        plugin = CTRF(config)
    setattr(config, '_ctrf', plugin)
    config.pluginmanager.register(plugin, name='ctrf_plugin')
    pass


def pytest_unconfigure(config: Config):
    ctrf = getattr(config, '_ctrf', None)
    if ctrf is not None:
        delattr(config, '_ctrf')
    if config.pluginmanager.hasplugin('ctrf_plugin'):
        config.pluginmanager.unregister(name='ctrf_plugin')


@fixture(autouse=True)
def ctrf_json_metadata(request: FixtureRequest):
    if not request.config.option.ctrf:
        return
    tags = list()
    for mark in request.node.iter_markers():
        tag = mark.name
        if tag == 'ctrf_suite':
            request.node._ctrf_metadata['suite'] = mark.args
        if mark.args:
            for arg in mark.args:
                tag += f'::{arg}'
        if mark.kwargs:
            for key, value in mark.kwargs.items():
                tag += f'::{key}_{value}'
        tags.append(tag)
    request.node._ctrf_metadata.setdefault('tags', tags)
    if hasattr(request.node, 'callspec'):
        browser = request.node.callspec.params.get('browser_name')
        if browser:
            request.node._ctrf_metadata.setdefault('browser', browser)
    return request.node._ctrf_metadata
