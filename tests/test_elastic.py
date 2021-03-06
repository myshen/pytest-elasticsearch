"""Pytest-elasticsearch tests."""
import pytest
from tempfile import gettempdir

from mock import patch

from pytest_elasticsearch import factories

ELASTICSEARCH_CONF_PATH_1_5_2 = '/opt/elasticsearch-1.5.2/config'
ELASTICSEARCH_CONF_PATH_2_4_6 = '/opt/elasticsearch-2.4.6/config'
ELASTICSEARCH_EXECUTABLE_1_5_2 = '/opt/elasticsearch-1.5.2/bin/elasticsearch'
ELASTICSEARCH_EXECUTABLE_2_4_6 = '/opt/elasticsearch-2.4.6/bin/elasticsearch'
ELASTICSEARCH_EXECUTABLE_5_6_7 = '/opt/elasticsearch-5.6.7/bin/elasticsearch'
ELASTICSEARCH_EXECUTABLE_6_2_3 = '/opt/elasticsearch-6.2.3/bin/elasticsearch'


def elasticsearch_fixture_factory(executable, proc_name, port, **kwargs):
    """Create elasticsearch fixture pairs."""
    proc = factories.elasticsearch_proc(executable, port=port, **kwargs)
    elasticsearch = factories.elasticsearch(proc_name)
    return proc, elasticsearch


elasticsearch_proc_1_5_2, elasticsearch_1_5_2 = elasticsearch_fixture_factory(
    ELASTICSEARCH_EXECUTABLE_1_5_2, 'elasticsearch_proc_1_5_2',
    port=None, configuration_path=ELASTICSEARCH_CONF_PATH_1_5_2
)
elasticsearch_proc_2_4_6, elasticsearch_2_4_6 = elasticsearch_fixture_factory(
    ELASTICSEARCH_EXECUTABLE_2_4_6, 'elasticsearch_proc_2_4_6',
    port=None, configuration_path=ELASTICSEARCH_CONF_PATH_2_4_6
)
elasticsearch_proc_5_6_7, elasticsearch_5_6_7 = elasticsearch_fixture_factory(
    ELASTICSEARCH_EXECUTABLE_5_6_7, 'elasticsearch_proc_5_6_7', port=None
)
elasticsearch_proc_6_2_3, elasticsearch_6_2_3 = elasticsearch_fixture_factory(
    ELASTICSEARCH_EXECUTABLE_6_2_3, 'elasticsearch_proc_6_2_3', port=None
)


@pytest.mark.parametrize('elasticsearch_proc_name', (
    'elasticsearch_proc_1_5_2',
    'elasticsearch_proc_2_4_6',
    'elasticsearch_proc_5_6_7',
    'elasticsearch_proc_6_2_3'
))
def test_elastic_process(request, elasticsearch_proc_name):
    """Simple test for starting elasticsearch_proc."""
    elasticsearch_proc = request.getfixturevalue(elasticsearch_proc_name)
    assert elasticsearch_proc.running() is True


@pytest.mark.parametrize('elasticsearch_name', (
    'elasticsearch_1_5_2',
    'elasticsearch_2_4_6',
    'elasticsearch_5_6_7',
    'elasticsearch_6_2_3'
))
def test_elasticsarch(request, elasticsearch_name):
    """Test if elasticsearch fixtures connects to process."""
    elasticsearch = request.getfixturevalue(elasticsearch_name)
    info = elasticsearch.cluster.health()
    assert info['status'] == 'green'


@pytest.mark.parametrize('executable, expected_version', (
    (ELASTICSEARCH_EXECUTABLE_1_5_2, '1.5.2'),
    (ELASTICSEARCH_EXECUTABLE_2_4_6, '2.4.6'),
    (ELASTICSEARCH_EXECUTABLE_5_6_7, '5.6.7'),
    (ELASTICSEARCH_EXECUTABLE_6_2_3, '6.2.3')
))
def test_version_extraction(executable, expected_version):
    """Verfiy if we can properly extract elasticsearch version."""
    assert '{major}.{minor}.{patch}'.format(
        **factories.get_version_parts(executable)
    ) == expected_version


elasticsearch_proc_random = factories.elasticsearch_proc(
    ELASTICSEARCH_EXECUTABLE_1_5_2, port=None,
    configuration_path=ELASTICSEARCH_CONF_PATH_1_5_2
)
elasticsearch_random = factories.elasticsearch('elasticsearch_proc_random')


def test_random_port(elasticsearch_random):
    """Test if elasticsearch fixture can be started on random port."""
    assert elasticsearch_random.cluster.health()['status'] == 'green'


def test_default_configuration(request):
    """Test default configuration."""
    config = factories.return_config(request)

    assert config['logsdir'] == gettempdir()
    assert not config['port']
    assert config['host'] == '127.0.0.1'
    assert not config['cluster_name']
    assert config['network_publish_host'] == '127.0.0.1'
    assert config['discovery_zen_ping_multicast_enabled'] == 'false'
    assert config['index_store_type'] == 'memory'
    assert config['logs_prefix'] == ''

    logsdir_ini = request.config.getini('elasticsearch_logsdir')
    logsdir_option = request.config.getoption('elasticsearch_logsdir')

    assert logsdir_ini == '/tmp'
    assert logsdir_option is None


@patch('pytest_elasticsearch.plugin.pytest.config')
def test_ini_option_configuration(request):
    """Test if ini and option configuration works in proper way."""
    request.config.getoption.return_value = None
    request.config.getini.return_value = '/test1'

    assert '/test1' == factories.return_config(request)['logsdir']

    request.config.getoption.return_value = '/test2'
    request.config.getini.return_value = None

    assert '/test2' == factories.return_config(request)['logsdir']


elasticsearch_proc_args = factories.elasticsearch_proc(
    ELASTICSEARCH_EXECUTABLE_1_5_2,
    configuration_path=ELASTICSEARCH_CONF_PATH_1_5_2,
    port=None, elasticsearch_logsdir='/tmp'
)


@patch('pytest_elasticsearch.plugin.pytest.config')
def test_fixture_arg_is_first(request, elasticsearch_proc_args):
    """Test if arg comes first than opt and ini."""
    request.config.getoption.return_value = '/test1'
    request.config.getini.return_value = '/test2'
    conf_dict = factories.return_config(request)

    port = elasticsearch_proc_args.port
    command = ' '.join(elasticsearch_proc_args.command_parts)
    path_logs = 'path.logs=/tmp/elasticsearch_{}_logs'.format(port)

    assert conf_dict['logsdir'] == '/test1'
    assert path_logs in command
