import unittest
from unittest.mock import patch, MagicMock

from oss_fuzz_hook import run_project


class TestOssFuzzHook(unittest.TestCase):

    @patch('oss_fuzz_hook.subprocess.run')
    def test_run_project_unknown_harness_type(self, mock_subprocess_run):
        """Test error handling for unknown harness type"""
        result = run_project(project="jupyter_server", harness_type="invalid_type")
        self.assertFalse(result)

    @patch('oss_fuzz_hook.subprocess.run')
    @patch('oss_fuzz_hook.os.path.exists')
    def test_run_project_no_fuzzers_directory(self, mock_exists, mock_subprocess_run):
        """Test error handling when fuzzers directory doesn't exist"""
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        mock_exists.return_value = False
        
        result = run_project(project="jupyter_server", harness_type="existing")
        self.assertFalse(result)

    @patch('oss_fuzz_hook.subprocess.run')
    @patch('oss_fuzz_hook.os.path.exists')
    @patch('oss_fuzz_hook.os.listdir')
    def test_run_project_no_fuzzers_found(self, mock_listdir, mock_exists, mock_subprocess_run):
        """Test error handling when no fuzzers are found"""
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        mock_exists.return_value = True
        mock_listdir.return_value = []
        
        result = run_project(project="jupyter_server", harness_type="existing")
        self.assertFalse(result)

    @patch('oss_fuzz_hook.subprocess.run')
    @patch('oss_fuzz_hook.os.path.exists')
    @patch('oss_fuzz_hook.os.listdir')
    def test_run_project_fuzzer_execution_fails(self, mock_listdir, mock_exists, mock_subprocess_run):
        """Test error handling when fuzzer execution fails"""
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0),  # pull_images
            MagicMock(returncode=0),  # build_image
            MagicMock(returncode=0),  # build_fuzzers
            MagicMock(returncode=1)   # run_fuzzer fails
        ]
        mock_exists.return_value = True
        mock_listdir.return_value = ["fuzz_serialization"]
        
        result = run_project(project="jupyter_server", harness_type="existing")
        self.assertTrue(result)  # Failure is logged, but should still return True


if __name__ == '__main__':
    unittest.main()