
import ntpath
import traceback
from aiowinreg.utils.regcmdpathcompleter import REGCMDPathCompleter
from aiowinreg.external.aiocmd.aiocmd import aiocmd
from aiowinreg import logger
from aiowinreg.ahive import AIOWinRegHive
from aiowinreg.filestruct.vk import REGTYPE
from aiowinreg.utils.afile import AFile

class WinRegReaderConsole(aiocmd.PromptToolkitCmd):
	def __init__(self, filepath = None):
		aiocmd.PromptToolkitCmd.__init__(self, ignore_sigint=False)
		self.filename = None
		self.filepath = filepath
		self.filehandle = None
		self.hive = None
		self.__current_path = None
		self.__current_path_keys = []
		self.__current_path_vals = []

	async def do_open(self, filepath = None):
		"""Opens a hive file"""
		try:
			if self.filehandle is not None:
				self.filehandle.close()
			if filepath is None and self.filepath is None:
				raise Exception('No filepath specified!')
			if filepath is not None:
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
		"""Lists all keys in the current path"""
		try:
			for key in await self.hive.enum_key(self.__current_path):
				print('[%s][ROOT\\%s\\%s]' % (self.filename, self.__current_path, key))
			
			return True, None
		except Exception as e:
			traceback.print_exc()
			print('LS failed! Reason: %s' % str(e))
			return False, e

	async def do_lsval(self):
		"""Lists all values in the current path"""
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
		"""Reads classes in the current path"""
		try:
			cl = await self.hive.get_class(self.__current_path)
			print(cl)
			return True, None
		except Exception as e:
			traceback.print_exc()
			print('CLASS failed! Reason: %s' % str(e))
			return False, e
	
	async def do_sd(self):
		"""Reads security descriptor in the current path"""
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
		"""Changes the current path"""
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
		"""Reads a value in the current path"""
		try:
			key = await self.hive.find_key(self.__current_path)
			if key is None:
				print('Key not found!')
				return False, None
			res = await self.hive.get_value(valuename, key = key)
			if res is None:
				print('Value not found!')
				return False, None
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
	
	async def do_walk(self, depth = 1):
		"""Recursively lists keys and values in the current path"""
		try:
			async for keypath in self.hive.walk(self.__current_path, depth = depth):
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
	
	# TODO: Fix this
	#async def do_search(self, pattern, in_keys = True, in_valuenames = True, in_values = True):
	#	async for x in self.hive.search(pattern, in_keys = True, in_valuenames = True, in_values = True):
	#		print(x)
	

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
