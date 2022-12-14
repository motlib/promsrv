"""Unittests for promexp module"""

# from datetime import datetime, timedelta

import pytest

from ..promexp import (PrometheusExporter, PrometheusExporterException,
                       UnknownMeasurementException)


def _has_line(promexp: PrometheusExporter, line: str) -> bool:
    """Utility function to check if rendered output contains a specific line."""

    out = promexp.render().split("\n")

    return any(map(lambda l: l == line, out))


@pytest.fixture(name="promexp")
def promexp_fixture() -> PrometheusExporter:
    """Create a new prometheus exporter instance."""

    return PrometheusExporter()


def test_promqtt_register(promexp: PrometheusExporter) -> None:
    """Register measurement and check that it's not yet in the output."""
    promexp.register(name="test_meas_1", datatype="gauge", helpstr="yeah", timeout=12)

    out = promexp.render().split("\n")

    # we did not set a value, so no measurement shall be visible
    hasline = any(map(lambda l: l.startswith("test_meas_1"), out))

    assert not hasline


def test_promqtt_register_twice(promexp: PrometheusExporter) -> None:
    """Double registration of a measurement raises an exception."""

    promexp.register(name="test_meas_1", datatype="gauge", helpstr="yeah", timeout=12)

    with pytest.raises(PrometheusExporterException):
        promexp.register(
            name="test_meas_1", datatype="gauge", helpstr="yeah", timeout=12
        )


def test_promqtt_set(promexp: PrometheusExporter) -> None:
    """Setting a value to a registered measurement works fine."""

    promexp.register(name="test_meas_1", datatype="gauge", helpstr="yeah", timeout=12)

    promexp.set(name="test_meas_1", value=12.3, labels={"foo": "bar"})

    print("*** Render Output  ***")
    print(promexp.render())

    assert _has_line(promexp, "# HELP test_meas_1 yeah")
    assert _has_line(promexp, "# TYPE test_meas_1 gauge")
    assert _has_line(promexp, 'test_meas_1{foo="bar"} 12.3')


def test_promqtt_unset(promexp: PrometheusExporter) -> None:
    """Setting a value of a registered metric to None removes it."""

    promexp.register(name="test_meas_1", datatype="gauge", helpstr="yeah", timeout=12)

    # Set to metric values with different labels
    promexp.set(name="test_meas_1", value=12.3, labels={"foo": "bar"})

    promexp.set(name="test_meas_1", value=12.3, labels={"foo": "foo"})

    promexp.set(name="test_meas_1", value=None, labels={"foo": "bar"})

    assert not _has_line(promexp, 'test_meas_1{foo="bar"}')


def test_promqtt_unset_new(promexp: PrometheusExporter) -> None:
    """Setting a value of a registered metric that was never set has no effect."""

    promexp.register(name="test_meas_1", datatype="gauge", helpstr="yeah", timeout=12)

    promexp.set(name="test_meas_1", value=None, labels={"foo": "bar"})

    assert not _has_line(promexp, 'test_meas_1{foo="bar"}')


def test_promqtt_not_registered(promexp: PrometheusExporter) -> None:
    """Setting a value to a not registered measurement raises an exception."""

    with pytest.raises(UnknownMeasurementException):
        promexp.set(name="test_meas_2", value=12.3, labels={})


# def test_promqtt_timeout(monkeypatch, promexp):
#    '''Check if timed out items are correctly removed.'''
#
#    promexp.register(
#        name='test_meas_1',
#        datatype='gauge',
#        helpstr='yeah',
#        timeout=12)
#
#    promexp.register(
#        name='test_meas_2',
#        datatype='gauge',
#        helpstr='yeah',
#        timeout=0)
#
#    # create dummy functions returning the current time or time 13s in the
#    # future to fake timeout.
#    dtm = datetime.now()
#
#    def tm_now():
#        return dtm
#
#    def tm_13s():
#        return dtm + timedelta(seconds=13)
#
#    #monkeypatch.setattr(..promexp, "_get_time", tm_now)
#
#    #promexp._get_time = tm_now # pylint: disable=protected-access
#    #promqtt.promexp._get_time = tm_now
#    promexp.set(
#        name='test_meas_1',
#        value=12.3,
#        labels={'foo': 'bar'})
#
#    # make sure it is rendered to the output
#    assert _has_line(promexp, 'test_meas_1{foo="bar"} 12.3')
#
#    #promexp._get_time = tm_13s # pylint: disable=protected-access
#    #monkeypatch.setattr(promqtt.promexp, "_get_time", tm_13s)
#
#
#    # make sure it is not rendered to the output anymore
#    assert not _has_line(promexp, 'test_meas_1{foo="bar"} 12.3')
#
#    # as there was only one item, also make sure that the header is removed
#    assert not _has_line(promexp, '# HELP yeah')
