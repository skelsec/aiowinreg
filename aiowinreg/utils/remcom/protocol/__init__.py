import enum
import json
import datetime
import ipaddress
import copy

class UniversalEncoder(json.JSONEncoder):
	"""
	Used to override the default json encoder to provide a direct serialization for formats
	that the default json encoder is incapable to serialize
	"""
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return obj.isoformat()
		elif isinstance(obj, enum.Enum):
			return obj.value
		elif isinstance(obj, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
			return str(obj)
		elif hasattr(obj, 'to_dict'):
			return obj.to_dict()
		else:
			return json.JSONEncoder.default(self, obj)

class COMMAND(enum.Enum):
	OK = 'OK'
	ERR = 'ERR'
	CONTINUE = 'CONTINUE'
	CLOSE = 'CLOSE'
	OPEN = 'OPEN'
	LS = 'LS'
	LSRES = 'LSRES'
	#SEARCH = 'SEARCH'

class CMD:
	@staticmethod
	def deserialize(d):
		# not safe, but this object is internal only
		obj = copy.deepcopy(cmd2obj[d['cmd']])
		for k in d:
			setattr(obj, k, d[k])
		return obj
	
	def to_dict(self):
		return self.__dict__

	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)

class CMDOK(CMD):
	def __init__(self, token:str):
		self.token = token
		self.cmd = COMMAND.OK

class CMDContinue(CMD):
	def __init__(self, token:str):
		self.token = token
		self.cmd = COMMAND.CONTINUE

class CMDERR(CMD):
	def __init__(self, token:str, reason:str):
		self.token = token
		self.reason = reason
		self.cmd = COMMAND.ERR

class CMDCLOSE(CMD):
	def __init__(self, token:str):
		self.token = token
		self.cmd = COMMAND.CLOSE

class CMDOPEN(CMD):
	def __init__(self, token:str, filepath:str):
		self.token = token
		self.filepath = filepath
		self.cmd = COMMAND.OPEN

class CMDLS(CMD):
	def __init__(self, token:str, regpath:str):
		self.token = token
		self.regpath = regpath
		self.cmd = COMMAND.LS

class CMDLSRES(CMD):
	def __init__(self, token:str):
		self.token = token
		self.cmd = COMMAND.LSRES
		self.keys = []
		self.values = []
		

cmd2obj = {
	COMMAND.OK : CMDOK,
	COMMAND.ERR : CMDERR,
	COMMAND.CONTINUE : CMDContinue,
	COMMAND.CLOSE : CMDCLOSE,
	COMMAND.OPEN : CMDOPEN,
	COMMAND.LS : CMDLS,
}