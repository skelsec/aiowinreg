
"""
Der vk-Record
=============

Offset	Size	Contents
0x0000	Word	ID: ASCII-"vk" = 0x6B76
0x0002	Word	name length
0x0004	D-Word	length of the data
0x0008	D-Word	Offset of Data
0x000C	D-Word	Type of value
0x0010	Word	Flag
0x0012	Word	Unused (data-trash)
0x0014	????	Name

If bit 0 of the flag-word is set, a name is present, otherwise the
value has no name (=default)
If the data-size is lower 5, the data-offset value is used to store
the data itself!
"""
import io
import enum

class REGTYPE(enum.Enum):
	REG_UNKNOWN = -1 #there are keytypes which are undocumented. If this type is used, you can access the actual value under value_type_raw
	REG_NONE = 0
	REG_SZ = 1
	REG_EXPAND_SZ = 2
	REG_BINARY = 3
	REG_DWORD =4
	REG_DWORD_BIG_ENDIAN = 5
	REG_LINK = 6
	REG_MULTI_SZ = 7 
	REG_RESOURCE_LIST = 8  
	REG_FULL_RESOURCE_DESCRIPTOR = 9
	REG_RESOURCE_REQUIREMENTS_LIST = 10
	REG_QWORD = 11

class NTRegistryVK:
	def __init__(self):
		self.magic = b'vk'
		self.name_length = None
		self.data_length = None
		self.offset_data = None
		self.value_type = None
		self.flag = None
		self.unused = None
		self.name = None
		
		####
		self.data = None
		self.data_fmt = None
		self.value_type_raw = None

	def format_data(self):
		#TODO: implement others
		if self.value_type == REGTYPE.REG_SZ:
			self.data_fmt = self.data.decode('utf-16-le').strip()
		elif self.value_type == REGTYPE.REG_MULTI_SZ:
			self.data_fmt = []
			for entry in self.data.split(b'\x00\x00\x00'):
				if len(entry) == 0 or entry == b'\x00\x00':
					continue
				self.data_fmt.append((entry + b'\x00\x00\x00').decode('utf-16-le').strip())
		elif self.value_type == REGTYPE.REG_DWORD:
			self.data_fmt = int.from_bytes(self.data, byteorder='little', signed = False)
		elif self.value_type == REGTYPE.REG_DWORD_BIG_ENDIAN:
			self.data_fmt = int.from_bytes(self.data, byteorder='big', signed = False)
		elif self.value_type == REGTYPE.REG_QWORD:
			self.data_fmt = int.from_bytes(self.data, byteorder='little', signed = False)
		else:
			self.data_fmt = self.data
		
		
	def load_data(self, reader, is_file = True):
		if self.data_length < 0:
			self.data_length = 0x7fffffff & self.data_length 
			
		if self.data_length == 0:
			self.data = b''
		elif self.data_length < 5:
			self.data = self.offset_data.to_bytes(4, 'little', signed = False)
		else:
			if is_file is True:
				reader.seek(self.offset_data+ 4 + 4096)
			else:
				reader.seek(self.offset_data+ 4)
			#self.data = reader.read(self.data_length+4) ###??? +4
			self.data = reader.read(self.data_length)
		self.format_data()
		return self.data_fmt

	async def aload_data(self, reader, is_file = True):
		if self.data_length < 0:
			self.data_length = 0x7fffffff & self.data_length 
			
		if self.data_length == 0:
			self.data = b''
		elif self.data_length < 5:
			self.data = self.offset_data.to_bytes(4, 'little', signed = False)
		else:
			if is_file is True:
				await reader.seek(self.offset_data+ 4 + 4096)
			else:
				await reader.seek(self.offset_data+ 4)
			res = await reader.read(self.data_length)
			if isinstance(res, tuple):
				self.data, err = res
				if err is not None:
					raise err
			else:
				self.data = res
			
		self.format_data()
		return self.data_fmt		

	@staticmethod
	def from_bytes(data):
		return NTRegistryVK.from_buffer(io.BytesIO(data))

	@staticmethod
	def from_buffer(buff):
		vk = NTRegistryVK()
		vk.magic = buff.read(2)
		vk.name_length = int.from_bytes(buff.read(2), 'little', signed = False)
		vk.data_length = int.from_bytes(buff.read(4), 'little', signed = True)
		vk.offset_data = int.from_bytes(buff.read(4), 'little', signed = False)

		t = int.from_bytes(buff.read(4), 'little', signed = False)
		vk.value_type_raw = t
		if t in [e.value for e in REGTYPE]:
			vk.value_type = REGTYPE(t)
		else:
			vk.value_type = REGTYPE.REG_UNKNOWN
			
		vk.flag = int.from_bytes(buff.read(2), 'little', signed = False)
		vk.unused = int.from_bytes(buff.read(2), 'little', signed = False)
		vk.name = buff.read(vk.name_length)

		return vk

	def __str__(self):
		t = '== NT Registry VK block ==\r\n'
		for k in self.__dict__:
			t += '%s: %s \r\n' % (k, self.__dict__[k])
		return t
