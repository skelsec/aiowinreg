
# https://bazaar.launchpad.net/~guadalinex-members/dumphive/trunk/view/head:/winreg.txt
# https://github.com/msuhanov/regf/blob/master/Windows%20registry%20file%20format%20specification.md
"""
0x00000000	D-Word	ID: ASCII-"regf" = 0x66676572
0x00000004	D-Word	????
0x00000008	D-Word	???? Always the same value as at 0x00000004
0x0000000C	Q-Word	last modify date in WinNT date-format
0x00000014	D-Word	1
0x00000018	D-Word	3
0x0000001C	D-Word	0
0x00000020	D-Word	1
0x00000024	D-Word	Offset of 1st key record
0x00000028	D-Word	Size of the data-blocks (Filesize-4kb)
0x0000002C	D-Word	1
0x000001FC	D-Word	Sum of all D-Words from 0x00000000 to 0x000001FB
"""
import io

class NTRegistryHeadr:
	def __init__(self):
		self.magic = b'regf'
		self.primary_sequence_number = None
		self.secondary_sequence_number = None
		self.last_modified = None
		self.version_major = None
		self.version_minor = None
		self.file_type = None
		self.file_format = None
		self.offset = None
		self.size = None
		self.clustering_factor = None
		self.file_name = None
		self.reserved = None
		self.checksum = None #XOR-32 checksum of the previous 508 bytes
		self.boot_type = None
		self.boot_recover = None

	def parse_header_bytes(self, data):
		self.parse_header_buffer(io.BytesIO(data))
	
	def parse_header_buffer(self, reader):
		self.magic = reader.read(4)
		self.primary_sequence_number = int.from_bytes(reader.read(4), 'little', signed = False)
		self.secondary_sequence_number = int.from_bytes(reader.read(4), 'little', signed = False)
		self.last_modified = reader.read(8)
		self.version_major = int.from_bytes(reader.read(4), 'little', signed = False)
		self.version_minor = int.from_bytes(reader.read(4), 'little', signed = False)
		self.file_type = int.from_bytes(reader.read(4), 'little', signed = False)
		self.file_format = int.from_bytes(reader.read(4), 'little', signed = False)
		self.offset = int.from_bytes(reader.read(4), 'little', signed = False)
		self.size = int.from_bytes(reader.read(4), 'little', signed = False)
		self.clustering_factor = int.from_bytes(reader.read(4), 'little', signed = False)
		try:
			self.file_name = reader.read(64).decode('utf-16-le').replace('\x00','')
		except:
			self.file_name = None
		self.reserved = reader.read(3576)
		self.checksum = int.from_bytes(reader.read(4), 'little', signed = False)
		self.boot_type = int.from_bytes(reader.read(4), 'little', signed = False)
		self.boot_recover = int.from_bytes(reader.read(4), 'little', signed = False)

	@staticmethod
	async def aread(reader):
		hdr = NTRegistryHeadr()
		res = await reader.read(4096)
		if isinstance(res, tuple):
			data, err = res
			if err is not None:
				raise err
		else:
			data = res
		hdr.parse_header_bytes(data)
		return hdr

	@staticmethod
	def read(reader):
		hdr = NTRegistryHeadr()
		hdr.parse_header_buffer(reader)
		return hdr

	def __str__(self):
		t = '== NT Registry header ==\r\n'
		for k in self.__dict__:
			t += '%s: %s \r\n' % (k, self.__dict__[k])
		return t