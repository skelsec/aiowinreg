
import asyncio
import ntpath
from aiowinreg.ahive import AIOWinRegHive
from aiowinreg.utils.afile import AFile
from aiowinreg.filestruct.vk import REGTYPE
from aiowinreg.utils.remcom.protocol import *
import traceback

class AIOWinRegRemoteControlServer:
	def __init__(self, in_q: asyncio.Queue, out_q: asyncio.Queue):
		self.filepath = None
		self.filename = None
		self.filehandle = None
		self.hive = None
		self.in_q : asyncio.Queue = in_q
		self.out_q : asyncio.Queue= out_q

	async def run(self):
		await self.__handle_in()

	async def __handle_in(self):
		while True:
			data = await self.in_q.get()
			cmd = CMD.deserialize(data)
			if cmd.cmd == COMMAND.OPEN:
				asyncio.create_task(self.do_open(cmd))
			if cmd.cmd == COMMAND.LS:
				asyncio.create_task(self.do_ls(cmd))
			if cmd.cmd == COMMAND.CLOSE:
				asyncio.create_task(self.do_close(cmd))
				return
	
	async def send_ok(self, cmd):
		await self.out_q.put(CMDOK(cmd.token))
	
	async def send_err(self, cmd, reason = 'WINREG Error'):
		await self.out_q.put(CMDERR(cmd.token, reason))

	async def do_open(self, cmd):
		try:
			self.filepath = cmd.filepath
			self.filename = ntpath.basename(self.filepath)
			self.filehandle = AFile(self.filepath)
			self.hive = AIOWinRegHive(self.filehandle)
			await self.send_ok(cmd)
		except Exception as e:
			await self.send_err(cmd, str(e))
			traceback.print_exc()

	
	async def do_ls(self, cmd: CMDLS):
		try:
			reply = CMDLSRES(cmd.token)
			for keypath in await self.hive.enum_key(cmd.regpath):
				reply.keys.append('%s\\%s' % (cmd.regpath, keypath))
			key = await self.hive.find_key(cmd.regpath)
			for valuename in await self.hive.list_values(key):
				valuename = valuename.decode()
				valuepath = cmd.regpath + '\\' + valuename
				res = await self.hive.get_value(valuename, key = key)
				valuetype, value = res
				if valuetype == REGTYPE.REG_UNKNOWN:
					reply.values.append((valuepath, valuetype.name, [value.hex()]))
					#print('[%s][ROOT\\%s][%s] %s' % (self.filename, valuepath, valuetype, value.hex()))
				if valuetype == REGTYPE.REG_MULTI_SZ:
					valres = []
					for i, val in enumerate(value):
						valres.append(val)
					reply.values.append((valuepath, valuetype.name, valuetype.name, valres.replace('\x00', '')))
						#print('[%s][ROOT\\%s][%s][%s] %s' % (self.filename, valuepath, valuetype.name, i, val))
				else:
					t = value
					if isinstance(value, bytes):
						t = t.hex()
					elif isinstance(value, str):
						t = t.replace('\x00', '')
					reply.values.append((valuepath, valuetype.name, [t]))
					#print('[%s][ROOT\\%s][%s] %s' % (self.filename, valuepath, valuetype.name, t))
			await self.out_q.put(reply.to_dict())
			await self.send_ok(cmd)
		except Exception as e:
			await self.send_err(cmd, str(e))
			traceback.print_exc()

	async def do_close(self, cmd):
		try:
			if self.filehandle is not None:
				await self.filehandle.close()
			await self.send_ok(cmd)
		except Exception as e:
			await self.send_err(cmd, str(e))
			traceback.print_exc()

async def testprint(out_q):
	while True:
		data = await out_q.get()
		print(data)

async def amain():
	regfile = 'SOFTWARE.reg'
	in_q = asyncio.Queue()
	out_q = asyncio.Queue()
	asyncio.create_task(testprint(out_q))

	srv = AIOWinRegRemoteControlServer(in_q, out_q)
	asyncio.create_task(srv.run())

	await in_q.put(CMDOPEN('1', regfile).to_dict())
	await in_q.put(CMDLS('2', 'Policies\\Microsoft\\Windows NT\\Terminal Services\\Client').to_dict())
	await in_q.put(CMDCLOSE('3').to_dict())
	await asyncio.sleep(100)



if __name__ == '__main__':
	asyncio.run(amain())