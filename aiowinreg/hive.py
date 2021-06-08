
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
		
	def close(self):
		self.reader.close()

	def setup(self):
		if self.header is None:
			self.header = NTRegistryHeadr.read(self.reader)
		if self.root is None:
			self.root = self.search_root_key()

	def search_root_key(self):
		
		if not self.root_hbin:
			self.reader.seek(4096, 0)
			hbin_offset = 4096
			offset_next = -1

			while offset_next != 0:
				self.reader.seek(hbin_offset,0)
				hbin = NTRegistryHbin.read(self.reader)
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
	
	def __load_cell_from_offset(self, offset, nk_partial=False):
		if offset not in self.__cells_lookup:
			cell = NTRegistryCell.load_data_from_offset(self.reader, offset, self.is_file, nk_partial=False)
			self.__cells_lookup[offset] = cell
		return self.__cells_lookup[offset]
		
	def __find_subkey(self, hash_rec, key_name):
		for _ in range(255):
			subkey = self.__load_cell_from_offset(hash_rec.offset_nk, nk_partial=True)
			if isinstance(subkey, NTRegistryHR):
				hash_rec = subkey
				continue
			elif isinstance(subkey, (NTRegistryRI, NTRegistryLH)):
				for thash_rec in subkey.hash_records:
					res = self.__find_subkey(thash_rec, key_name)
					if res is not None:
						return res
				
			else:
				if subkey.name.upper() == key_name.upper():
					return subkey
			return

	def find_subkey(self, parent, key_name):
		if self.root is None:
			self.setup()
		
		key = self.__load_cell_from_offset(parent.offset_lf_stable)
		if key is None:
			return None
		
		if isinstance(key, NTRegistryRI):
			for thash_rec in key.hash_records:
				res = self.__find_subkey(thash_rec, key_name)
				if res is not None:
					return res

		for offset in key.get_key_offsets(key_name):
			rec = self.__load_cell_from_offset(offset)
			if rec.name.upper() == key_name.upper():
				return rec
				
		return None
		
	def find_key(self, key_path, throw = True):
		if self.root is None:
			self.setup()
		if len(key_path) < 2:
			return self.root
		
		if key_path not in self.__key_lookup:
			working_path = ''
			parent_key = self.root
			for key in key_path.split('\\'):
				skey = self.find_subkey(parent_key, key)
				if skey is None:
					if throw is True:
						raise Exception('Could not find subkey! Full path: %s Working path: %s Missing key name: %s' % (key_path, working_path, key))
					else:
						return None
				working_path += '\\%s' % key
				parent_key = skey
			self.__key_lookup[key_path] = parent_key
		return self.__key_lookup[key_path]
		
	def enum_key(self, key_path, throw = True):
		if self.root is None:
			self.setup()
		names = []
		key = self.find_key(key_path, throw)
		if key.subkey_cnt_stable > 0:
			rec = self.__load_cell_from_offset(key.offset_lf_stable, nk_partial=False)
			for hash_rec in rec.hash_records:
				names += self.__get_name(hash_rec)

		return names

	def __get_name(self, hash_rec):
		names = []
		for _ in range(255):
			subkey = self.__load_cell_from_offset(hash_rec.offset_nk, nk_partial=False)
			if isinstance(subkey, NTRegistryHR):
				hash_rec = subkey
				continue
			elif isinstance(subkey, (NTRegistryRI, NTRegistryLH)):
				for thash_rec in subkey.hash_records:
					names += self.__get_name(thash_rec)
				break
			else:
				if subkey is None:
					break
				names.append(subkey.name)
				break

		return names

	def list_values(self, key):
		if self.root is None:
			self.setup()
		values = []
		if key.value_cnt <= 0:
			return values
		vl = ValueList.load_data_from_offset(self.reader, key.offset_value_list, key.value_cnt + 1, self.is_file)
		for record_offset in vl.record_offsets:
			if record_offset < 0:
				#print('Skipping value because offset smaller than 0! %s ' % record_offset)
				continue
			block = self.__load_cell_from_offset(record_offset, nk_partial=False)
			if not block:
				continue
			if block.flag == 0:
				values.append(b'default')
			else:
				values.append(block.name)
			
		return values
		
	def get_value(self, value_path, throw = True, key = None):
		if self.root is None:
			self.setup()
		
		if key is None:
			if value_path.find('\t') != -1:
				key_path, value_name = value_path.split('\t', 1)
			else:
				key_path = ntpath.dirname(value_path)
				value_name = ntpath.basename(value_path)
			key = self.find_key(key_path, throw)
		else:
			value_name = value_path
		
		if key is None:
			return None
		if key.value_cnt <= 0:
			return None
		
		vl = ValueList.load_data_from_offset(self.reader, key.offset_value_list, key.value_cnt + 1, self.is_file)
		for record_offset in vl.record_offsets:
			if record_offset < 0:
				continue
			block = self.__load_cell_from_offset(record_offset, nk_partial=False)
			if not block:
				continue
			if block.flag == 0:
				if value_name == 'default':
					return (block.value_type, block.load_data(self.reader, is_file = self.is_file))
			elif value_name == block.name.decode():
				return (block.value_type, block.load_data(self.reader, is_file = self.is_file))
				
		raise Exception('Could not find %s' % value_path)
		
	def get_class(self, key_path, throw = True):
		if self.root is None:
			self.setup()
		key = self.find_key(key_path, throw)

		if key is None:
			return None
		
		if key.offset_classname > 0:
			if self.is_file is True:
				self.reader.seek(key.offset_classname + 4096 + 4, 0)
			else:
				self.reader.seek(key.offset_classname + 4, 0)
			return self.reader.read(key.class_name_length).decode('utf-16-le')

	
	def get_sd(self, key):
		if self.root is None:
			self.setup()
		
		sk = self.__load_cell_from_offset(key.offset_sk, nk_partial=False)
		return sk.sd
	
	def walk(self, path, depth = -1):
		depth -= 1
		if depth == 0:
			return
			
		for key in self.enum_key(path):
			if path == '':
				np = key
			else:
				np = path + '\\' + key
			yield np
			for res in self.walk(np, depth):
				yield res
	
	def search(self, pattern, in_keys = True, in_valuenames = True, in_values = True):
		for keypath in self.walk('', -1):
			if in_keys is True:
				if keypath.find(pattern) != -1:
					yield keypath
			if in_valuenames or in_values is True:
				key = self.find_key(keypath)
				for valuename in self.list_values(key):
					valuename = valuename.decode()
					valuepath = keypath + '\\' + valuename
					if in_valuenames is True and valuename.find(pattern) != -1:
						yield valuepath
					
					if in_values is True:
						valuetype, value = self.get_value(valuename, key = key)
						
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