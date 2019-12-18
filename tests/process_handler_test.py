import pytest
from exit_pipe import ProcessHandler


class TestProcessHandler:
    @staticmethod
    def _get_process_handler():
        return ProcessHandler(['sh', '-c', 'exit', '0'])

    def test_init(self):
        process_handler = self._get_process_handler()
        assert not process_handler.force_exit
        assert process_handler.exit_code is None
        assert process_handler.subprocess is None

    @pytest.mark.parametrize(
        ('exit_code', 'bitfield_mapping', 'expected_exit_code'),
        (
            (0, '3:-1', 0),
            (1, '3:-1', -1),
            (2, '3:-1', -1),
            (3, '3:-1', -1),
            (0, '1,2:-1', 0),
            (1, '1,2:-1', -1),
            (2, '1,2:-1', -1),
            (3, '1,2:-1', -1),
        ))
    def test_bitfield_single_mapping(self, exit_code, bitfield_mapping, expected_exit_code):
        process_handler = self._get_process_handler()
        process_handler.exit_code = exit_code
        assert process_handler.pipe_bitfield(bitfield_mapping) == expected_exit_code

    @pytest.mark.parametrize(
        ('exit_code', 'bitfield_mapping', 'expected_exit_code'),
        (
            (0, '3:-1;12:-2', 0),
            (1, '3:-1;12:-2', -1),
            (2, '3:-1;12:-2', -1),
            (4, '3:-1;12:-2', -2),
            (8, '3:-1;12:-2', -2),
            (12, '3:-1;12:-2', -2),
        ))
    def test_bitfield_multiple_mappings(self, exit_code, bitfield_mapping, expected_exit_code):
        process_handler = self._get_process_handler()
        process_handler.exit_code = exit_code
        assert process_handler.pipe_bitfield(bitfield_mapping) == expected_exit_code

    @pytest.mark.parametrize(
        ('exit_code', 'bitfield_mapping', 'expected_exit_code'),
        (
            (1, '1:-1;1:-2', -1),
            (5, '1,2:-1;4,8:-2', -1),
            (10, '1,2:-1;4,8:-2', -1),
        ))
    def test_bitfield_multiple_mappings_first_match(self, exit_code, bitfield_mapping, expected_exit_code):
        process_handler = self._get_process_handler()
        process_handler.exit_code = exit_code
        assert process_handler.pipe_bitfield(bitfield_mapping) == expected_exit_code
