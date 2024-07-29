import sys, os
project_home = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

import unittest
import mock
import json
import requests

from adsputils import load_config

import adsdocmatch.utils as utils

config = load_config(proj_home=project_home)

class TestDocMatch(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_dedup_pairs(self):

        generic_pair_array = [("abc", "def"), ("ghi", "jkl"), ("mno", "pqr"),
                              ("stu", "abc"), ("ghi", "vwx"), ("abc", "def")]

        dedup_iter_1_result = [("abc", "def"), ("ghi", "jkl"), ("mno", "pqr")]
        dedup_remainder_1_result = [("stu", "abc"), ("ghi", "vwx")]

        (dedup_test, dedup_remainder) = utils.dedup_pairs(generic_pair_array)
        self.assertEqual(dedup_test, dedup_iter_1_result)
        self.assertEqual(dedup_remainder, dedup_remainder_1_result)

        dedup_iter_2_result = [("stu", "abc"), ("ghi", "vwx")]
        dedup_remainder_2_result = []

        (dedup_test, dedup_remainder) = utils.dedup_pairs(dedup_remainder)
        self.assertEqual(dedup_test, dedup_iter_2_result)
        self.assertEqual(dedup_remainder, dedup_remainder_2_result)

        pathological_case = [("abc", "def"), ("abc", "abc")]

        dedup_result = [("abc", "def")]
        dedup_remainder_result = [("abc", "abc")]

        (dedup_test, dedup_remainder) = utils.dedup_pairs(pathological_case)
        self.assertEqual(dedup_test, dedup_result)
        self.assertEqual(dedup_remainder, dedup_remainder_result)

    def test_read_user_submitted(self):
        user_sub_test_file = os.path.dirname(__file__) + "/stubdata/user_submitted.list"        
        input_pairs_result = [("2024ABCDE9999L...1T", "2024QRSTU1111....1T"),
                              ("2020ABCDE9995L...1T", "2019QRSTU1107....1T"),
                              ("2013arXiv1305.1234T", "2013ApJ..8888Q...1T"),
                              ("hello", "world")]
        input_pairs_test, failed_lines = utils.read_user_submitted(user_sub_test_file)
        self.assertEqual(input_pairs_test, input_pairs_result)
