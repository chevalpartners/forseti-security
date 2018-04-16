# Copyright 2017 The Forseti Security Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests the GCS inventory summary upload notifier."""


import mock
import unittest

from datetime import datetime

from google.cloud.forseti.common.util import string_formats
from google.cloud.forseti.notifier.notifiers import base_notification
from google.cloud.forseti.notifier.notifiers import gcs_inv_summary
from tests.unittest_utils import ForsetiTestCase


class GcsInvSummaryTest(ForsetiTestCase):
    """Tests for gcs_inv_summary_notifier."""

    def setUp(self):
        """Setup."""
        ForsetiTestCase.setUp(self)
        self.fake_utcnow = datetime(year=1920, month=5, day=6, hour=7, minute=8)

    def tearDown(self):
        """Tear down method."""
        ForsetiTestCase.tearDown(self)

    @mock.patch(
        'google.cloud.forseti.notifier.notifiers.gcs_inv_summary.date_time',
        autospec=True)
    def test_get_output_filename(self, mock_date_time):
        """Test_get_output_filename()."""
        mock_date_time.get_utc_now_datetime = mock.MagicMock()
        mock_date_time.get_utc_now_datetime.return_value = self.fake_utcnow
        expected_timestamp = self.fake_utcnow.strftime(
            string_formats.TIMESTAMP_TIMEZONE_FILES)

        gvp = gcs_inv_summary.GcsInvSummary('abcd', [], dict())
        actual = gvp._get_output_filename(string_formats.INV_SUMMARY_CSV_FMT)
        expexted = string_formats.INV_SUMMARY_CSV_FMT.format(
                gvp.inv_index_id, expected_timestamp)
        self.assertEquals(expexted, actual)

    @mock.patch(
        'google.cloud.forseti.notifier.notifiers.gcs_inv_summary.date_time',
        autospec=True)
    def test_get_output_filename_with_json(self, mock_date_time):
        """Test_get_output_filename()."""
        mock_date_time.get_utc_now_datetime = mock.MagicMock()
        mock_date_time.get_utc_now_datetime.return_value = self.fake_utcnow
        expected_timestamp = self.fake_utcnow.strftime(
            string_formats.TIMESTAMP_TIMEZONE_FILES)

        gvp = gcs_inv_summary.GcsInvSummary('abcd', [], dict())
        actual = gvp._get_output_filename(string_formats.INV_SUMMARY_JSON_FMT)
        expexted = string_formats.INV_SUMMARY_JSON_FMT.format(
                gvp.inv_index_id, expected_timestamp)
        self.assertEquals(expexted, actual)

    @mock.patch(
        'google.cloud.forseti.common.gcp_api.storage.StorageClient',
        autospec=True)
    @mock.patch('tempfile.NamedTemporaryFile')
    @mock.patch('google.cloud.forseti.common.data_access.csv_writer.os')
    def test_run(self, mock_os, mock_tempfile, mock_storage):
        """Test run()."""
        fake_tmpname = 'tmp_name'
        fake_output_name = 'abc'

        gvp = gcs_inv_summary.GcsInvSummary('abcd', [], dict(gcs_path='gs://x'))
        gvp._get_output_filename = mock.MagicMock(return_value=fake_output_name)
        gcs_path = '{}/{}'.format(
            gvp.notifier_config['gcs_path'], fake_output_name)

        mock_tmp_csv = mock.MagicMock()
        mock_tempfile.return_value = mock_tmp_csv
        mock_tmp_csv.name = fake_tmpname
        mock_tmp_csv.write = mock.MagicMock()

        gvp.run()

        mock_tmp_csv.write.assert_called()
        mock_storage.return_value.put_text_file.assert_called_once_with(
            fake_tmpname, gcs_path)

    @mock.patch(
        'google.cloud.forseti.common.gcp_api.storage.StorageClient',
        autospec=True)
    @mock.patch('google.cloud.forseti.common.util.parser.json_stringify')
    @mock.patch('google.cloud.forseti.common.data_access.csv_writer.write_csv')
    def test_run_with_json(self, mock_write_csv, mock_json_stringify,
        mock_storage):
        """Test run() with json file format."""
        mock_json_stringify.return_value = 'test123'

        config = dict(gcs_path='gs://x', data_format='json')
        gvp = gcs_inv_summary.GcsInvSummary('abcd', [], config)

        gvp._get_output_filename = mock.MagicMock()
        gvp.run()

        self.assertTrue(gvp._get_output_filename.called)
        self.assertEquals(
            string_formats.INV_SUMMARY_JSON_FMT,
            gvp._get_output_filename.call_args[0][0])
        self.assertFalse(mock_write_csv.called)
        self.assertTrue(mock_json_stringify.called)

    @mock.patch(
        'google.cloud.forseti.common.gcp_api.storage.StorageClient',
        autospec=True)
    @mock.patch('google.cloud.forseti.common.util.parser.json_stringify')
    @mock.patch('google.cloud.forseti.common.data_access.csv_writer.write_csv')
    def test_run_with_invalid_data_format(self, mock_write_csv,
        mock_json_stringify, mock_storage):
        """Test run() with json file format."""
        config = dict(gcs_path='gs://x', data_format='blah')
        gvp = gcs_inv_summary.GcsInvSummary('abcd', [], config)
        gvp._get_output_filename = mock.MagicMock()

        with self.assertRaises(base_notification.InvalidDataFormatError):
            gvp.run()

        self.assertFalse(gvp._get_output_filename.called)
        self.assertFalse(mock_write_csv.called)
        self.assertFalse(mock_json_stringify.called)

if __name__ == '__main__':
    unittest.main()
