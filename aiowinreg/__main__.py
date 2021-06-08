
import asyncio
import ntpath
import shlex
import traceback
from aiowinreg.utils.regcmdpathcompleter import REGCMDPathCompleter
from aiowinreg.external.aiocmd.aiocmd import aiocmd
from aiowinreg import logger
from aiowinreg.ahive import AIOWinRegHive
from aiowinreg.filestruct.vk import REGTYPE
from aiowinreg.utils.afile import AFile

class WinRegReaderConsole(aiocmd.PromptToolkitCmd):
	def __init__(self, filepath = None):
		aiocmd.PromptToolkitCmd.__init__(self, ignore_sigint=False) #Setting this to false, since True doesnt work on windows...
		self.filename = None
		self.filepath = filepath
		self.filehandle = None
		self.hive = None
		self.__current_path = None
		self.__current_path_keys = []
		self.__current_path_vals = []

	async def do_open(self, filepath ):
		"""Connects to the remote machine"""
		try:
			if self.filehandle is not None:
				self.filehandle.close()

			self.filepath = filepath
			self.filename = ntpath.basename(self.filepath)
			self.filehandle = AFile(self.filepath)
			self.hive = AIOWinRegHive(self.filehandle)
			self.__current_path = ''
			self.prompt = '[%s][ROOT]> ' % self.filename
			print('File opened!')
			await self.do_cd('')
			return True, None
		except Exception as e:
			traceback.print_exc()
			print('Open failed! Reason: %s' % str(e))
			return False, e

	async def do_ls(self):
		try:
			for key in await self.hive.enum_key(self.__current_path):
				print('[%s][ROOT\\%s\\%s]' % (self.filename, self.__current_path, key))
			
			return True, None
		except Exception as e:
			traceback.print_exc()
			print('LS failed! Reason: %s' % str(e))
			return False, e

	async def do_lsval(self):
		try:
			key = await self.hive.find_key(self.__current_path)
			await self.__lsval(self.__current_path, key)
			return True, None
		except Exception as e:
			traceback.print_exc()
			print('LSVAL failed! Reason: %s' % str(e))
			return False, e

	async def __lsval(self, basepath, key):
		try:
			for valuename in await self.hive.list_values(key):
				valuename = valuename.decode()
				valuepath = basepath + '\\' + valuename
				res = await self.hive.get_value(valuename, key = key)
				valuetype, value = res
				if valuetype == REGTYPE.REG_UNKNOWN:
					print('[%s][ROOT\\%s][%s] %s' % (self.filename, valuepath, valuetype, value.hex()))
				if valuetype == REGTYPE.REG_MULTI_SZ:
					for i, val in enumerate(value):
						print('[%s][ROOT\\%s][%s][%s] %s' % (self.filename, valuepath, valuetype.name, i, val))
				else:
					t = value
					if isinstance(value, bytes):
						t = t.hex()
					print('[%s][ROOT\\%s][%s] %s' % (self.filename, valuepath, valuetype.name, t))
			
			return True, None
		except Exception as e:
			traceback.print_exc()
			print('LSVAL inner failed! Reason: %s' % str(e))
			return False, e

	async def do_class(self):
		try:
			cl = await self.hive.get_class(self.__current_path)
			print(cl)
			return True, None
		except Exception as e:
			traceback.print_exc()
			print('CLASS failed! Reason: %s' % str(e))
			return False, e
	
	async def do_sd(self):
		try:
			key = await self.hive.find_key(self.__current_path)
			sd = await self.hive.get_sd(key)
			print(sd.to_sddl())
			return True, None
		except Exception as e:
			traceback.print_exc()
			print('SD failed! Reason: %s' % str(e))
			return False, e
	

	async def do_cd(self, path):
		try:
			if path == '.':
				return True, None

			if self.__current_path == '':
				if path == '..':
					print('You are in root!')
					return True, None
				self.__current_path = path
			else:
				if path == '..':
					if self.__current_path.find('\\') == -1:
						self.__current_path = ''
					else:
						self.__current_path = self.__current_path.split('\\', 1)[0]
				else:
					if path.startswith('\\') is False:
						self.__current_path += '\\' + path
					else:
						self.__current_path += path
			
			self.__current_path_keys = []
			for key in await self.hive.enum_key(self.__current_path):
				self.__current_path_keys.append(key)

			self.__current_path_vals = []
			tkey = await self.hive.find_key(self.__current_path)
			for valname in await self.hive.list_values(tkey):	
				self.__current_path_vals.append(valname.decode())


			self.prompt = '[%s][ROOT\\%s]> ' % (self.filename, self.__current_path)
			return True, None

		except Exception as e:
			traceback.print_exc()
			print('LS failed! Reason: %s' % str(e))
			return False, e

	async def do_cat(self, valuename):
		try:
			key = await self.hive.find_key(self.__current_path)
			res = await self.hive.get_value(valuename, key = key)
			valuetype, value = res
			if valuetype == REGTYPE.REG_UNKNOWN:
				print('%s: %s' % (valuetype, value))
			if valuetype == REGTYPE.REG_MULTI_SZ:
				for i, val in enumerate(value):
					print('%s[%s]: %s' % (valuetype, i, val))
			else:
				t = value
				if isinstance(value, bytes):
					t = t.hex()
				print('%s: %s' % (valuetype.name, t))
			return True, None
		except Exception as e:
			traceback.print_exc()
			print('CAT failed! Reason: %s' % str(e))
			return False, e
	
	async def do_walk(self):
		try:
			async for keypath in self.hive.walk(self.__current_path):
				print('[%s][ROOT\\%s]' % (self.filename, keypath))
				key = await self.hive.find_key(keypath)
				_, err = await self.__lsval(keypath, key)
				if err is not None:
					raise err
			return True, None
		except Exception as e:
			traceback.print_exc()
			print('WALK failed! Reason: %s' % str(e))
			return False, e
	
	async def do_search(self, pattern, in_keys = True, in_valuenames = True, in_values = True):
		async for x in self.hive.search(pattern, in_keys = True, in_valuenames = True, in_values = True):
			print(x)
	

	def get_current_keys(self):
		if self.__current_path is None:
			return []
		return list(self.__current_path_keys)
	
	def get_current_vals(self):
		if self.__current_path is None:
			return []
		return list(self.__current_path_vals)

	def _cd_completions(self):
		return REGCMDPathCompleter(get_current_dirs = self.get_current_keys)
	
	def _cat_completions(self):
		return REGCMDPathCompleter(get_current_dirs = self.get_current_vals)


async def amain(args):
	console = WinRegReaderConsole()
	if len(args.file) == 1:
		await console.do_open(args.file[0])
	if len(args.cmds) == 0:
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
	parser.add_argument('file', nargs=1)
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