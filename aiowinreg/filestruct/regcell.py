from aiowinreg.filestruct.keytypes import NTRegistryKeyTypes

class NTRegistryCell:
	def __init__(self):
		self.size = None
		self.data = None
	
	@staticmethod
	def load_data_from_offset(reader, offset):
		"""
		Returns a HBIN block from the data in the reader at offset
		"""
		reader.seek(4096+offset,0)
		cell = NTRegistryCell.read(reader)
		return cell.data

	@staticmethod
	def read(reader):
		cell = NTRegistryCell()
		cell.size = int.from_bytes(reader.read(4), 'little', signed = True)
		cell.size = cell.size * -1
		if cell.size == 0:
			return cell
		elif cell.size > 0:
			cell.data = reader.read(cell.size - 4)
			#input(cell.size)
			#input(cell.data[:2])
			if cell.data[:2] in NTRegistryKeyTypes:
				cell.data = NTRegistryKeyTypes[cell.data[:2]].from_bytes(cell.data)
			
		else:
			#deleted cell
			cell.data = reader.read( (-1)*cell.size - 4)

		return cell

	def __str__(self):
		t = '== NT Registry Cell struct ==\r\n'
		for k in self.__dict__:
			t += '%s: %s \r\n' % (k, self.__dict__[k])
		return t
