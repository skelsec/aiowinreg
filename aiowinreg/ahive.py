import ntpath

from aiowinreg.filestruct.header import NTRegistryHeadr
from aiowinreg.filestruct.hbin import NTRegistryHbin
from aiowinreg.filestruct.nk import NTRegistryNK, NKFlag
from aiowinreg.filestruct.regcell import NTRegistryCell
from aiowinreg.filestruct.valuelist import ValueList
from aiowinreg.filestruct.hashrecord import NTRegistryHR
from aiowinreg.filestruct.lh import NTRegistryLH
from aiowinreg.filestruct.ri import NTRegistryRI
from aiowinreg.filestruct.vk import REGTYPE


class AIOWinRegHive:
	"""
	Async version of the hive parser
	"""
	def __init__(self, reader, root_hbin = None, is_file = True):
		self.reader = reader
		self.header = None
		self.root = None
		self.root_hbin = root_hbin
		self.is_file = is_file
		if root_hbin is not None:
			self.header = NTRegistryHeadr()
		
		self.__cells_lookup = {}
		self.__key_lookup = {}
		
	async def close(self):
		await self.reader.close()

	async def setup(self):
		if self.header is None:
			self.header = await NTRegistryHeadr.aread(self.reader)
		if self.root is None:
			self.root = await self.search_root_key()

	async def search_root_key(self):
		
		if not self.root_hbin:
			await self.reader.seek(4096, 0)
			hbin_offset = 4096
			offset_next = -1

			while offset_next != 0:
				await self.reader.seek(hbin_offset,0)
				hbin = await NTRegistryHbin.aread(self.reader)
				for cell in hbin.cells:
					if isinstance(cell.data, NTRegistryNK):
						if NKFlag.ROOT in cell.data.flags:
							self.root_hbin = hbin
							return cell.data
				hbin_offset += hbin.offset_next
				offset_next = hbin.offset_next
		else:
			for cell in self.root_hbin.cells:
				if isinstance(cell.data, NTRegistryNK):
					if NKFlag.ROOT in cell.data.flags:
						return cell.data

		raise Exception('Could not find root key!')
	
	async def __load_cell_from_offset(self, offset, nk_partial=False):
		if offset not in self.__cells_lookup:
			cell = await NTRegistryCell.aload_data_from_offset(self.reader, offset, self.is_file, nk_partial=False)
			self.__cells_lookup[offset] = cell
		return self.__cells_lookup[offset]
	
	async def __find_subkey(self, hash_rec, key_name):
		for _ in range(255):
			subkey = await self.__load_cell_from_offset(hash_rec.offset_nk, nk_partial=True)
			if isinstance(subkey, NTRegistryHR):
				hash_rec = subkey
				continue
			elif isinstance(subkey, (NTRegistryRI, NTRegistryLH)):
				for thash_rec in subkey.hash_records:
					res = await self.__find_subkey(thash_rec, key_name)
					if res is not None:
						return res
				
			else:
				if subkey.name.upper() == key_name.upper():
					return subkey
			return
		
		
	async def find_subkey(self, parent, key_name):
		if self.root is None:
			await self.setup()
		key = await self.__load_cell_from_offset(parent.offset_lf_stable)
		if key is None:
			return None
		
		if isinstance(key, NTRegistryRI):
			for thash_rec in key.hash_records:
				res = await self.__find_subkey(thash_rec, key_name)
				if res is not None:
					return res

		for offset in key.get_key_offsets(key_name):
			rec = await self.__load_cell_from_offset(offset)
			if rec.name.upper() == key_name.upper():
				return rec
				
		return None	
		
	async def find_key(self, key_path, throw = True):
		if self.root is None:
			await self.setup()
		if len(key_path) < 2:
			return self.root
			
		working_path = ''
		parent_key = self.root
		for key in key_path.split('\\'):
			skey = await self.find_subkey(parent_key, key)
			if skey is None:
				if throw is True:
					raise Exception('Could not find subkey! Full path: %s Working path: %s Missing key name: %s' % (key_path, working_path, key))
				else:
					return None
			working_path += '\\%s' % key
			parent_key = skey
		return parent_key
		
	async def enum_key(self, key_path, throw = True):
		if self.root is None:
			await self.setup()
		names = []
		key = await self.find_key(key_path, throw)
		if key.subkey_cnt_stable > 0:
			rec = await self.__load_cell_from_offset(key.offset_lf_stable, nk_partial=False)
			for hash_rec in rec.hash_records:
				names += await self.__get_name(hash_rec)
		
		return names
		
		
	async def list_values(self, key):
		if self.root is None:
			await self.setup()
		values = []
		if key.value_cnt <= 0:
			return values
		vl = await ValueList.aload_data_from_offset(self.reader, key.offset_value_list, key.value_cnt + 1, self.is_file)
		for record_offset in vl.record_offsets:
			if record_offset < 0:
				#print('Skipping value because offset smaller than 0! %s ' % record_offset)
				continue
			block = await NTRegistryCell.aload_data_from_offset(self.reader, record_offset, self.is_file)
			if not block:
				continue
			if block.flag == 0:
				values.append(b'default')
			else:
				values.append(block.name)
			
		return values

	
	async def __get_name(self, hash_rec):
		names = []
		for _ in range(255):
			subkey = await self.__load_cell_from_offset(hash_rec.offset_nk, nk_partial=False)
			if isinstance(subkey, NTRegistryHR):
				hash_rec = subkey
				continue
			elif isinstance(subkey, (NTRegistryRI, NTRegistryLH)):
				for thash_rec in subkey.hash_records:
					names += await self.__get_name(thash_rec)
				break
			else:
				if subkey is None:
					break
				names.append(subkey.name)
				break

		return names
		
	async def get_value(self, value_path, throw = True, key = None):
		if self.root is None:
			await self.setup()
		if key is None:
			if value_path.find('\t') != -1:
				key_path, value_name = value_path.split('\t', 1)
			else:
				key_path = ntpath.dirname(value_path)
				value_name = ntpath.basename(value_path)
			key = await self.find_key(key_path, throw)
		else:
			value_name = value_path
		
		if key is None:
			return None
		if key.value_cnt <= 0:
			return None
		
		vl = await ValueList.aload_data_from_offset(self.reader, key.offset_value_list, key.value_cnt + 1, self.is_file)
		for record_offset in vl.record_offsets:
			if record_offset < 0:
				#print('Skipping value because offset smaller than 0! %s ' % record_offset)
				continue
			block = await NTRegistryCell.aload_data_from_offset(self.reader, record_offset, self.is_file)
			if not block:
				continue
			if block.flag == 0:
				if value_name == 'default':
					data = await block.aload_data(self.reader, is_file = self.is_file)
					return (block.value_type, data)
			elif value_name == block.name.decode():
				data = await block.aload_data(self.reader, is_file = self.is_file)
				return (block.value_type, data)
				
		raise Exception('Could not find %s' % value_path)
		
	async def get_class(self, key_path, throw = True):
		if self.root is None:
			await self.setup()
		key = await self.find_key(key_path, throw)

		if key is None:
			return None
		
		if key.offset_classname > 0:
			if self.is_file is True:
				await self.reader.seek(key.offset_classname + 4096 + 4, 0)
			else:
				await self.reader.seek(key.offset_classname + 4, 0)
			res = await self.reader.read(key.class_name_length)
			if isinstance(res, tuple):
				data, err = res
				if err is not None:
					raise err
			else:
				data = res
			return data.decode('utf-16-le')

	async def get_sd(self, key):
		if self.root is None:
			await self.setup()
		
		sk = await self.__load_cell_from_offset(key.offset_sk, nk_partial=False)
		return sk.sd

	async def walk(self, path, depth = -1):
		depth -= 1
		if depth == 0:
			return
			
		for key in await self.enum_key(path):
			if path == '':
				np = key
			else:
				np = path + '\\' + key
			yield np
			async for res in self.walk(np, depth):
				yield res
	
	async def search(self, pattern, in_keys = True, in_valuenames = True, in_values = True):
		async for keypath in self.walk('', -1):
			if in_keys is True:
				if keypath.find(pattern) != -1:
					yield keypath
			if in_valuenames or in_values is True:
				key = await self.find_key(keypath)
				for valuename in await self.list_values(key):
					valuename = valuename.decode()
					valuepath = keypath + '\\' + valuename
					if in_valuenames is True and valuename.find(pattern) != -1:
						yield valuepath
					
					if in_values is True:
						res = await self.get_value(valuename, key = key)
						valuetype, value = res
						if valuetype == REGTYPE.REG_UNKNOWN and value.hex().find(pattern) != -1:
							yield valuepath
						elif valuetype == REGTYPE.REG_MULTI_SZ:
							for i, val in enumerate(value):
								if val.find(pattern) != -1:
									yield valuepath
									break
						else:
							t = value
							if isinstance(value, bytes):
								t = t.hex()
							if str(value).find(pattern) != -1:
								yield valuepath