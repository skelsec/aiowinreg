
# https://bazaar.launchpad.net/~guadalinex-members/dumphive/trunk/view/head:/winreg.txt
"""
hbin-Header
===========

Offset	Size	Contents
0x0000	D-Word	ID: ASCII-"hbin" = 0x6E696268
0x0004	D-Word	Offset from the 1st hbin-Block
0x0008	D-Word	Offset to the next hbin-Block
0x001C	D-Word	Block-size

The values in 0x0008 and 0x001C should be the same, so I don't know
if they are correct or swapped...

From offset 0x0020 inside a hbin-block data is stored with the following
format:


Offset	Size	Contents
0x0000	D-Word	Data-block size
0x0004	????	Data

"""

from aiowinreg.filestruct.regcell import NTRegistryCell

class NTRegistryHbin:
	def __init__(self):
		self.magic = b'hbin'
		self.offset_first = None
		self.offset_next = None
		self.block_size = None

		self.cells = []

	@staticmethod
	def read(reader):
		hbin = NTRegistryHbin()
		hbin.magic = reader.read(4)
		hbin.offset_first = int.from_bytes(reader.read(4), 'little', signed = False)
		hbin.offset_next = int.from_bytes(reader.read(4), 'little', signed = False)
		hbin.block_size = int.from_bytes(reader.read(4), 'little', signed = False)
		reader.read(16)
		
		cell = NTRegistryCell.read(reader)
		hbin.cells.append(cell)
		while cell.size != 0:
			cell = NTRegistryCell.read(reader)
			hbin.cells.append(cell)

		return hbin

	def __str__(self):
		t = '== NT Registry HBIN struct ==\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], list):
				for i, item in enumerate(self.__dict__[k]):
					t += '   %s: %s: %s' % (k, i, str(item))
			else:
				t += '%s: %s \r\n' % (k, str(self.__dict__[k]))
		return t