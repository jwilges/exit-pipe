'''exit-pipe: a command-line utility to pipe the exit code from a subprocess through one or more modifiers'''
import logging
import signal
import subprocess
import sys
from typing import List
from argparse import ArgumentParser, REMAINDER

__version__ = '1.0.0'
_logger = logging.getLogger(__name__)


class ProcessHandler:
    '''A lightweight API to execute a subprocess and pipe subprocess exit code state through
    one or more modifiers'''
    def __init__(self, subprocess_arguments: List[str]):
        self.force_exit = False
        self.exit_code = None
        self.subprocess = None
        self.subprocess_arguments = subprocess_arguments

        def sigint_handler(_signal: int, _frame):
            self.force_exit = True
        signal.signal(signal.SIGINT, sigint_handler)

    def pipe_bitfield(self, bitfield_mappings: str):
        '''Return a modified process exit code based on one or more bitfield mappings

        For example, if `bitfield` is `"3:1;12:0"` or `"1,2:1;4,8:0"`:
        - exit codes 1 and 2 will map to 1, while
        - exit codes 4 and 8 will map to 0.'''
        mappings = bitfield_mappings.strip().split(';')
        for mapping in mappings:
            masks, mapped_exit_code = mapping.strip().split(':')
            masks = [int(mask.strip()) for mask in masks.split(',')]
            mapped_exit_code = int(mapped_exit_code.strip())
            try:
                mask_match = next(mask for mask in masks if bool(self.exit_code & mask))
                _logger.debug('bitfield mask match: %d; exit code: %d -> %d',
                              mask_match, self.exit_code, mapped_exit_code)
                return mapped_exit_code
            except StopIteration:
                pass
        return self.exit_code

    def run(self):
        '''Run the configured subprocess and store its exit state'''
        self.force_exit = False
        self.exit_code = None
        self.subprocess = subprocess.Popen(self.subprocess_arguments, universal_newlines=True,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while self.subprocess.poll() is None:
            if self.force_exit:
                _logger.debug('forwarding SIGINT to subprocess')
                self.subprocess.send_signal(signal.SIGINT)
            try:
                process_stdout, process_stderr = self.subprocess.communicate(timeout=0.25)
                print(process_stdout, file=sys.stdout, sep=None)
                print(process_stderr, file=sys.stderr, sep=None)
            except subprocess.TimeoutExpired:
                continue
        self.exit_code = self.subprocess.returncode


def main():
    '''`exit-pipe` command-line entry point'''
    parser = ArgumentParser(description=__doc__.partition('\n')[0])
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--bitfield', type=str)
    parser.add_argument('command')
    parser.add_argument('arguments', nargs=REMAINDER)
    arguments = parser.parse_args()

    logging_level = logging.WARNING - (10 * arguments.verbose)
    logging.basicConfig(level=logging_level)

    process_handler = ProcessHandler([arguments.command, *arguments.arguments])
    process_handler.run()

    if process_handler.force_exit:
        _logger.error('subprocess was interrupted')
        sys.exit(1)

    if process_handler.exit_code is None:
        _logger.error('subprocess exit code is unknown')
        sys.exit(1)

    if arguments.bitfield:
        exit_code = process_handler.pipe_bitfield(arguments.bitfield)

    if process_handler.exit_code != exit_code:
        _logger.info('%s: exit code: %d -> %d', arguments.command, process_handler.exit_code, exit_code)
    else:
        _logger.info('%s: exit code: %d', arguments.command, process_handler.exit_code)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
