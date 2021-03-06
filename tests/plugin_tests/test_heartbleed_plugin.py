# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import unittest

import pickle

from sslyze.plugins.heartbleed_plugin import HeartbleedPlugin, HeartbleedScanCommand
from sslyze.server_connectivity_tester import ServerConnectivityTester
from sslyze.ssl_settings import ClientAuthenticationServerConfigurationEnum

from tests.openssl_server import VulnerableOpenSslServer


class HeartbleedPluginTestCase(unittest.TestCase):

    def test_heartbleed_good(self):
        server_test = ServerConnectivityTester(hostname='www.google.com')
        server_info = server_test.perform()

        plugin = HeartbleedPlugin()
        plugin_result = plugin.process_task(server_info, HeartbleedScanCommand())

        self.assertFalse(plugin_result.is_vulnerable_to_heartbleed)

        self.assertTrue(plugin_result.as_text())
        self.assertTrue(plugin_result.as_xml())

        # Ensure the results are pickable so the ConcurrentScanner can receive them via a Queue
        self.assertTrue(pickle.dumps(plugin_result))

    @unittest.skipIf(not VulnerableOpenSslServer.is_platform_supported(), 'Not on Linux 64')
    def test_heartbleed_bad(self):
        with VulnerableOpenSslServer() as server:
            server_test = ServerConnectivityTester(hostname=server.hostname, ip_address=server.ip_address,
                                                 port=server.port)
            server_info = server_test.perform()

            plugin = HeartbleedPlugin()
            plugin_result = plugin.process_task(server_info, HeartbleedScanCommand())

        self.assertTrue(plugin_result.is_vulnerable_to_heartbleed)
        self.assertTrue(plugin_result.as_text())
        self.assertTrue(plugin_result.as_xml())

        # Ensure the results are pickable so the ConcurrentScanner can receive them via a Queue
        self.assertTrue(pickle.dumps(plugin_result))

    @unittest.skipIf(not VulnerableOpenSslServer.is_platform_supported(), 'Not on Linux 64')
    def test_succeeds_when_client_auth_failed(self):
        # Given a server that requires client authentication
        with VulnerableOpenSslServer(
                client_auth_config=ClientAuthenticationServerConfigurationEnum.REQUIRED
        ) as server:
            # And the client does NOT provide a client certificate
            server_test = ServerConnectivityTester(
                hostname=server.hostname,
                ip_address=server.ip_address,
                port=server.port
            )
            server_info = server_test.perform()

            # The plugin works even when a client cert was not supplied
            plugin = HeartbleedPlugin()
            plugin_result = plugin.process_task(server_info, HeartbleedScanCommand())

        self.assertTrue(plugin_result.is_vulnerable_to_heartbleed)
        self.assertTrue(plugin_result.as_text())
        self.assertTrue(plugin_result.as_xml())
