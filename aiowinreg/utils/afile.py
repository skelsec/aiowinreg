
class AFile:
	def __init__(self, filepath):
		self.filepath = filepath
		self.fd = open(filepath, 'rb')
		
	async def seek(self, pos, whence = 0):
		return self.fd.seek(pos, whence)
	
	async def read(self, n = -1):
		return self.fd.read(n)
	
	async def close(self):
		return self.fd.close()
	
	