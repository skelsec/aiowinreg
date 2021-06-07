from aiowinreg.filestruct.nk import NTRegistryNK
from aiowinreg.filestruct.keytypes import NTRegistryKeyTypes

class NTRegistryCell:
	def __init__(self):
		self.size = None
		self.data = None
	
	@staticmethod
	def load_data_from_offset(reader, offset, is_file = True, nk_partial = False):
		"""
		Returns a HBIN block from the data in the reader at offset
		"""
		if is_file is True:
			reader.seek(4096+offset,0)
		else:
			reader.seek(offset,0)
		cell = NTRegistryCell.read(reader, nk_partial = nk_partial)
		return cell.data

	@staticmethod
	async def aload_data_from_offset(reader, offset, is_file = True, nk_partial = False):
		"""
		Async
		Returns a HBIN block from the data in the reader at offset
		"""
		if is_file is True:
			await reader.seek(4096+offset,0)
		else:
			await reader.seek(offset,0)
		cell = await NTRegistryCell.aread(reader, nk_partial = nk_partial)
		return cell.data

	@staticmethod
	async def aread(reader, nk_partial = False):
		cell = NTRegistryCell()
		res = await reader.read(4)
		if isinstance(res, tuple):
			t, err = res
			if err is not None:
				raise err
		else:
			t = res

		if t == b'hbin':
			cell.size = 0
			return cell

		cell.size = int.from_bytes(t, 'little', signed = True)
		cell.size = cell.size * -1
		
		if cell.size == 0:
			return cell
		elif cell.size > 0:
			res = await reader.read(cell.size - 4)
			if isinstance(res, tuple):
				cell.data, err = res
				if err is not None:
					raise err
			else:
				cell.data = res

			if cell.data[:2] in NTRegistryKeyTypes:
				if cell.data[:2] == b'nk' and nk_partial is True:
					#this is a hack to speed up key search
					cell.data = NTRegistryNK.nameparse(cell.data)
				else:
					cell.data = NTRegistryKeyTypes[cell.data[:2]].from_bytes(cell.data)
			
		else:
			res = await reader.read( (-1)*cell.size - 4)
			if isinstance(res, tuple):
				cell.data, err = res
				if err is not None:
					raise err
			else:
				cell.data = res

		return cell

	@staticmethod
	def read(reader, nk_partial = False):
		cell = NTRegistryCell()
		t = reader.read(4)
		if t == b'hbin':
			cell.size = 0
			return cell
		cell.size = int.from_bytes(t, 'little', signed = True)
		cell.size = cell.size * -1
		if cell.size == 0:
			return cell
		elif cell.size > 0:
			cell.data = reader.read(cell.size - 4)
			if cell.data[:2] in NTRegistryKeyTypes:
				if cell.data[:2] == b'nk' and nk_partial is True:
					#this is a hack to speed up key search
					cell.data = NTRegistryNK.nameparse(cell.data)
				else:
					cell.data = NTRegistryKeyTypes[cell.data[:2]].from_bytes(cell.data)
			
		else:
			cell.data = reader.read( (-1)*cell.size - 4)

		return cell

	def __str__(self):
		t = '== NT Registry Cell struct ==\r\n'
		for k in self.__dict__:
			t += '%s: %s \r\n' % (k, self.__dict__[k])
		return t
