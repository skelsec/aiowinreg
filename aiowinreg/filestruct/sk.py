from winacl.dtyp.security_descriptor import SECURITY_DESCRIPTOR

"""

"""
import io

class NTRegistrySK:
	def __init__(self):
		self.magic = b'sk'
		self.unknown = None
		self.offset_prev = None
		self.offset_next = None
		self.reference_cnt = None
		self.sd_size = None
		self.sd = None

	@staticmethod
	def from_bytes(data):
		return NTRegistrySK.from_buffer(io.BytesIO(data))

	@staticmethod
	def from_buffer(buff):
		sk = NTRegistrySK()
		sk.magic = buff.read(2)
		sk.unknown = int.from_bytes(buff.read(2), 'little', signed = False)
		sk.offset_prev = int.from_bytes(buff.read(4), 'little', signed = False)
		sk.offset_next = int.from_bytes(buff.read(4), 'little', signed = False)
		sk.reference_cnt = int.from_bytes(buff.read(4), 'little', signed = False)
		sk.sd_size = int.from_bytes(buff.read(4), 'little', signed = False)
		if sk.sd_size > 15:
			sk.sd = SECURITY_DESCRIPTOR.from_bytes(buff.read(sk.sd_size))
		return sk

	def __str__(self):
		t = '== NT Registry SK block ==\r\n'
		for k in self.__dict__:
			t += '%s: %s \r\n' % (k, self.__dict__[k])
		return t