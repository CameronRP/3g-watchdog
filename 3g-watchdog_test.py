"""
3g-watchdog - monitors 3G connectivity and takes action if it's down
Copyright (C) 2018, The Cacophony Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import imp
import pytest
import subprocess

# Importing like this is necessary to because the source file we're
# testing starts with a number and doesn't have a .py extension.
with open('3g-watchdog') as module_file:
    watchdog = imp.load_source("watchdog", "3g-watchdog", module_file)


def test_not_using_3g(run_once, sleep, is_defroute_via_dev, ping_host, reboot):
    is_defroute_via_dev.return_value = False

    watchdog.main()

    sleep.assert_called_once_with(300)
    is_defroute_via_dev.assert_called_once_with('usb0')
    assert ping_host.called is False
    assert reboot.called is False


def test_ping_ok(run_once, sleep, is_defroute_via_dev, ping_host, reboot):
    is_defroute_via_dev.return_value = True
    ping_host.return_value = True

    watchdog.main()

    sleep.assert_called_once_with(300)
    is_defroute_via_dev.assert_called_once_with('usb0')
    ping_host.assert_called_once_with("8.8.8.8")
    assert reboot.called is False


def test_ping_fails(run_once, sleep, is_defroute_via_dev, ping_host, reboot):
    is_defroute_via_dev.return_value = True
    ping_host.return_value = False

    watchdog.main()

    sleep.assert_called_once_with(300)
    is_defroute_via_dev.assert_called_once_with('usb0')
    assert ping_host.call_count == 2 * 5  # 2 hosts, 5 retries
    reboot.assert_called_once_with()


def test_ping_fails(run_once, sleep, is_defroute_via_dev, ping_host, reboot):
    is_defroute_via_dev.return_value = True
    ping_host.return_value = False

    watchdog.main()

    sleep.assert_called_once_with(300)
    is_defroute_via_dev.assert_called_once_with('usb0')
    assert ping_host.call_count == 2 * 5  # 2 hosts, 5 retries
    reboot.assert_called_once_with()


def test_some_pings_fail(run_once, sleep, is_defroute_via_dev, ping_host,
                         reboot):
    is_defroute_via_dev.return_value = True
    ping_host.side_effect = [False] * 5 + [True] * 50

    watchdog.main()

    sleep.assert_called_once_with(300)
    is_defroute_via_dev.assert_called_once_with('usb0')
    assert ping_host.call_count == 5 + 1
    assert reboot.call_count == 0


def test_is_defroute_via_dev_no_usb0(check_output):
    m = check_output.return_value = """\
default via 192.168.164.1 dev wlan0  proto static  metric 600
169.254.0.0/16 dev eth0  scope link  metric 1000 linkdown
"""
    assert watchdog.is_defroute_via_dev('usb0') is False


def test_is_defroute_via_dev_via_usb0(check_output):
    m = check_output.return_value = """\
default via 192.168.164.1 dev usb0  proto static  metric 600
169.254.0.0/16 dev eth0  scope link  metric 1000 linkdown
"""
    assert watchdog.is_defroute_via_dev('usb0') is True

    # Check alternate ordering
    m = check_output.return_value = """\
169.254.0.0/16 dev eth0  scope link  metric 1000 linkdown
default via 192.168.164.1 dev usb0  proto static  metric 600
"""
    assert watchdog.is_defroute_via_dev('usb0') is True


def test_is_defroute_via_dev_usb0_not_default(check_output):
    m = check_output.return_value = """\
1.2.3.0/24 via 192.168.164.1 dev usb0  proto static  metric 600
169.254.0.0/16 dev eth0  scope link  metric 1000 linkdown
"""
    assert watchdog.is_defroute_via_dev('usb0') is False


def test_ping_host(check_call):
    assert watchdog.ping_host("1.2.3.4") is True

    check_call.assert_called_once_with(
        ['ping', '-n', '-q', '-c1', '-w30', '1.2.3.4'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_ping_host_failed(check_call):
    check_call.side_effect = subprocess.CalledProcessError(1, None)

    assert watchdog.ping_host("1.2.3.4") is False


def test_reboot(check_call):
    watchdog.reboot()

    check_call.assert_called_once_with(['/sbin/reboot'])


@pytest.fixture
def run_once(mocker):
    m = mocker.patch.object(watchdog, "running", autospec=True)
    m.side_effect = [True, False]
    return m


@pytest.fixture
def sleep(mocker):
    return mocker.patch.object(watchdog.time, "sleep", autospec=True)


@pytest.fixture
def is_defroute_via_dev(mocker):
    return mocker.patch.object(watchdog, "is_defroute_via_dev", autospec=True)


@pytest.fixture
def ping_host(mocker):
    return mocker.patch.object(watchdog, "ping_host", autospec=True)


@pytest.fixture
def reboot(mocker):
    return mocker.patch.object(watchdog, "reboot", autospec=True)


@pytest.fixture
def check_call(mocker):
    return mocker.patch.object(
        watchdog.subprocess, "check_call", autospec=True)


@pytest.fixture
def check_output(mocker):
    return mocker.patch.object(
        watchdog.subprocess, "check_output", autospec=True)
