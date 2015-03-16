# -*- coding:utf-8 -*-
#
# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import stat
import unittest

import bad_config_domains
import good_config_domains
import mock

from anchor import app
from anchor import jsonloader


class TestValidDN(unittest.TestCase):
    def setUp(self):
        self.expected_key_permissions = (stat.S_IRUSR | stat.S_IFREG)
        super(TestValidDN, self).setUp()

    def tearDown(self):
        pass

    def test_self_test(self):
        self.assertTrue(True)

    def test_config_check_domains_good(self):
        self.assertEqual(app.validate_config(good_config_domains), None)

    def test_config_check_domains_bad(self):
        self.assertRaises(
            app.ConfigValidationException,
            app.validate_config,
            bad_config_domains
        )

    def test_check_file_permissions_good(self):
        config = {'return_value.st_mode': (stat.S_IRUSR | stat.S_IFREG)}
        with mock.patch("os.stat", **config):
            app._check_file_permissions("/mock/path")

    def test_check_file_permissions_bad(self):
        config = {'return_value.st_mode': (stat.S_IWOTH | stat.S_IFREG)}
        with mock.patch("os.stat", **config):
            self.assertRaises(app.ConfigValidationException,
                              app._check_file_permissions, "/mock/path")

    def test_validate_config_no_auth(self):
        jsonloader.conf.load_str_data("{}")
        self.assertRaisesRegexp(app.ConfigValidationException,
                                "No authentication configured",
                                app.validate_config, jsonloader.conf)

    def test_validate_config_no_ca(self):
        jsonloader.conf.load_str_data("""{"auth" : { "static": {}} }""")
        self.assertRaisesRegexp(app.ConfigValidationException,
                                "No ca configuration present",
                                app.validate_config, jsonloader.conf)

    def test_validate_config_ca_config_reqs(self):
        ca_config_requirements = ["cert_path", "key_path", "output_path",
                                  "signing_hash", "valid_hours"]

        config = """{"auth" : { "static": {}},
                     "ca": { "cert_path":"", "key_path":"", "output_path":"",
                            "signing_hash":"", "valid_hours":""} }"""

        # Iterate through the ca_config_requirements, replace each one in turn
        # with 'missing_req', perform validation. Each should raise in turn
        for req in ca_config_requirements:
            jsonloader.conf.load_str_data(config.replace(req, "missing_req"))
            self.assertRaisesRegexp(app.ConfigValidationException,
                                    "CA config missing: %s" % req,
                                    app.validate_config, jsonloader.conf)

    @mock.patch('os.path.isfile')
    def test_validate_config_no_ca_cert_file(self, isfile):
        json_config = """{"auth" : { "static": {}},
                     "ca": { "cert_path":"no_cert_file",
                     "key_path":"no_key_file", "output_path":"",
                     "signing_hash":"", "valid_hours":""} } """
        jsonloader.conf.load_str_data(json_config)
        isfile.return_value = False
        self.assertRaisesRegexp(app.ConfigValidationException,
                                "could not read file: no_cert_file",
                                app.validate_config, jsonloader.conf)

    @mock.patch('os.path.isfile')
    @mock.patch('os.access')
    @mock.patch('os.stat')
    def test_validate_config_no_validators(self, stat, access, isfile):
        config = """{"auth" : { "static": {}},
                     "ca": { "cert_path":"no_cert_file",
                             "key_path":"no_key_file",
                             "output_path":"","signing_hash":"",
                             "valid_hours":""} } """
        jsonloader.conf.load_str_data(config)
        isfile.return_value = True
        access.return_value = True
        stat.return_value.st_mode = self.expected_key_permissions
        self.assertRaisesRegexp(app.ConfigValidationException,
                                "No validators configured",
                                app.validate_config, jsonloader.conf)

    def test_validate_config_good(self):
        pass
