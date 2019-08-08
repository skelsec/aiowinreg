
import ntpath

from aiowinreg.filestruct.header import NTRegistryHeadr
from aiowinreg.filestruct.hbin import NTRegistryHbin
from aiowinreg.filestruct.nk import NTRegistryNK, NKFlag
from aiowinreg.filestruct.regcell import NTRegistryCell
from aiowinreg.filestruct.valuelist import ValueList


class AIOWinRegHive:
	def __init__(self, reader):
		self.reader = reader
		self.header = None
		self.root = None
		
	def close(self):
		self.reader.close()

	def setup(self):
		self.header = NTRegistryHeadr.read(self.reader)
		self.root = self.search_root_key()

	def search_root_key(self):
		self.reader.seek(4096, 0)
		hbin_offset = 4096
		offset_next = -1

		while offset_next != 0:
			self.reader.seek(hbin_offset,0)
			hbin = NTRegistryHbin.read(self.reader)
			for cell in hbin.cells:
				if isinstance(cell.data, NTRegistryNK):
					if NKFlag.ROOT in cell.data.flags:
						return cell.data
			hbin_offset += hbin.offset_next
			offset_next = hbin.offset_next


		raise Exception('Could not find root key!')		
		
		
	def find_subkey(self, parent, key_name):
		if self.root is None:
			self.setup()
		key = NTRegistryCell.load_data_from_offset(self.reader, parent.offset_lf_stable)
		for offset in key.get_key_offsets(key_name):
			rec = NTRegistryCell.load_data_from_offset(self.reader,offset)
			if rec.name == key_name:
					return rec
				
		return None
		
	def find_key(self, key_path, throw = True):
		if self.root is None:
			self.setup()
		if len(key_path) < 2:
			return self.root
			
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
		return parent_key
		
	def enum_key(self, key_path, throw = True):
		if self.root is None:
			self.setup()
		names = []
		key = self.find_key(key_path, throw)
		if key.subkey_cnt_stable > 0:
			rec = NTRegistryCell.load_data_from_offset(self.reader,key.offset_lf_stable)
			for hash_rec in rec.hash_records:
				subkey = NTRegistryCell.load_data_from_offset(self.reader,hash_rec.offset_nk)
				names.append(subkey.name)
		
		return names
		
		
	def list_values(self, key):
		if self.root is None:
			self.setup()
		values = []
		if key.value_cnt <= 0:
			return values
		vl = ValueList.load_data_from_offset(self.reader, key.offset_value_list, key.value_cnt + 1)
		for record_offset in vl.record_offsets:
			block = NTRegistryCell.load_data_from_offset(self.reader, record_offset)
			if not block:
				continue
			if block.flag == 0:
				values.append(b'default')
			else:
				values.append(block.name)
			
		return values
		
	def get_value(self, value_path, throw = True):
		if self.root is None:
			self.setup()
		key_path = ntpath.dirname(value_path)
		value_name = ntpath.basename(value_path)
		
		key = self.find_key(key_path, throw)
		if key is None:
			return None
		if key.value_cnt <= 0:
			return None
		
		vl = ValueList.load_data_from_offset(self.reader, key.offset_value_list, key.value_cnt + 1)
		for record_offset in vl.record_offsets:
			block = NTRegistryCell.load_data_from_offset(self.reader, record_offset)
			if not block:
				continue
			if block.flag == 0:
				if value_name == 'default':
					return (block.value_type, block.load_data(self.reader))
			elif value_name == block.name.decode():
				return (block.value_type, block.load_data(self.reader))
				
		raise Exception('Could not find %s' % value_path)
		
	def get_class(self, key_path, throw = True):
		if self.root is None:
			self.setup()
		key = self.find_key(key_path, throw)

		if key is None:
			return None
		
		if key.offset_classname > 0:
			self.reader.seek(key.offset_classname + 4096 + 4, 0)
			return self.reader.read(key.class_name_length).decode('utf-16-le')