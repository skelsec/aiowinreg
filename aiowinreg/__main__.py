
import asyncio
import shlex
from aiowinreg import logger
from aiowinreg._version import __banner__
from aiowinreg.examples.console import WinRegReaderConsole

async def amain(args):
	console = WinRegReaderConsole()
	if len(args.cmds) == 0:
		print(__banner__)
		print("Usage:\nUse 'load' to load a hive file)\nType '?' for help\n")
		await console.run()
		return
	
	for command in args.cmds:
		if command == 'i':
			await console.run()
			return
			
		cmd = shlex.split(command)
		_, err = await console._run_single_command(cmd[0], cmd[1:])
		if err is not None:
			raise err

def main():
	import argparse
	import platform
	import logging
	
	parser = argparse.ArgumentParser(description='Windows Registry hive browser')
	parser.add_argument('-v', '--verbose', action='count', default=0)
	parser.add_argument('cmds', nargs='*')
	
	args = parser.parse_args()

	if args.verbose >=1:
		logger.setLevel(logging.DEBUG)

	if args.verbose > 2:
		logger.setLevel(1) #enabling deep debug
		asyncio.get_event_loop().set_debug(True)
		logging.basicConfig(level=logging.DEBUG)

	asyncio.run(amain(args))

if __name__ == '__main__':
	main()