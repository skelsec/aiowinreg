import pathlib
import pytest
import asyncio
from aiowinreg.hive import AIOWinRegHive

CURRENT_FILE_PATH = pathlib.Path(__file__).parent.absolute()
REG_DIR = CURRENT_FILE_PATH.joinpath('testdata')
REGHIVE_NAMES = ['sam.reg', 'security.reg', 'system.reg', 'software.reg']

def open_file(path):
    return open(path, 'rb')

def setup_test(reghive):
	try:
		reghive.setup()
		assert reghive.header is not None
		assert reghive.root is not None
		return True, None
	except Exception as e:
		return None, e

def fullwalk_test(reghive, maxiter=1000):
	try:
		for keypath in reghive.walk(''):
			maxiter -= 1
			if maxiter == 0:
				break
			key = reghive.find_key(keypath, throw=True)			
			keyclass = reghive.get_class(keypath, True)
			assert keyclass is not None
			sd = reghive.get_sd(key)
			assert sd is not None
			values = reghive.list_values(key)
			assert values is not None
			x = reghive.enum_key(keypath, throw=True)
			assert x is not None
		return True, None
	except Exception as e:
		#import traceback
		#traceback.print_exc()
		return None, e

def sam_test(samhive):
	try:
		f = samhive.get_value(r'SAM\Domains\Account\F')
		assert f is not None
		v = samhive.get_value(r'SAM\Domains\Account\V')
		assert v is not None
		names = samhive.enum_key(r'SAM\Domains\Account\Users')
		assert names is not None
		assert len(names) > 0
		for rid in names:
			if rid == 'Names':
				continue
			key_path = 'SAM\\Domains\\Account\\Users\\%s\\V' % rid
			uac_data = samhive.get_value(key_path)
			assert uac_data is not None

		return True, None
	except Exception as e:
		#import traceback
		#traceback.print_exc()
		return None, e
	
def security_test(securityhive, skip_iter=False):
	try:
		value = securityhive.get_value('Policy\\PolEKList\\default', False)
		if value is None:
			value = securityhive.get_value('Policy\\PolSecretEncryptionKey\\default', throw=True)
		assert value is not None

		value = securityhive.get_value('Policy\\Secrets\\NL$KM\\CurrVal\\default')
		assert value is not None

		cache_reg = securityhive.find_key('Cache', False)
		assert cache_reg is not None

		if skip_iter is True:
			# Skip this test on Windows 2008
			record = securityhive.get_value('Cache\\NL$IterationCount')
			assert record is not None

		keys = securityhive.enum_key('Policy\\Secrets')
		assert keys is not None

		return True, None
	except Exception as e:
		return None, e
	
def system_test(systemhive):
	try:
		ccs = systemhive.get_value('Select\\Current')
		assert ccs is not None
		ccs = ccs[1]
		currentcontrol = "ControlSet%03d" % ccs
		for key in ['JD', 'Skew1', 'GBG', 'Data']:
			x = systemhive.get_class('%s\\Control\\Lsa\\%s' % (currentcontrol, key))
			assert x is not None

		return True, None
	except Exception as e:
		return None, e

def software_test(softwarehive):
	try:
		x = softwarehive.get_value(r'Microsoft\Windows NT\CurrentVersion\Winlogon\DefaultUserName')
		assert x is not None
		assert len(x) > 0
		x = softwarehive.get_value(r'Microsoft\Windows NT\CurrentVersion\Winlogon\DefaultDomainName')
		assert x is not None
		assert len(x) > 0
		x = softwarehive.get_value(r'Microsoft\Windows NT\CurrentVersion\Winlogon\DefaultPassword')
		assert x is not None
		assert len(x) > 0

		return True, None
	except Exception as e:
		return None, e

def test_2008_32_setup():
    hives = {}
    for regname in REGHIVE_NAMES:
        hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008_32', regname)))
    
    for regname, reghive in hives.items():
        _, err = setup_test(reghive)
        assert err is None

def test_2008_32_fullwalk():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008_32', regname)))
	
	for regname, reghive in hives.items():
		_, err = setup_test(reghive)
		assert err is None

	for regname, reghive in hives.items():
		_, err = fullwalk_test(reghive)
		assert err is None


def test_2008_32_sam():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008_32', regname)))
	
	_, err = sam_test(hives['sam.reg'])
	assert err is None


def test_2008_32_security():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008_32', regname)))
	
	_, err = security_test(hives['security.reg'])
	assert err is None


def test_2008_32_system():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008_32', regname)))
	
	_, err = system_test(hives['system.reg'])
	assert err is None

#
#def test_2008_32_software():
#	hives = {}
#	for regname in REGHIVE_NAMES:
#		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008_32', regname)))
#	
#	_, err = software_test(hives['software.reg'])
#	assert err is None


def test_2008r2_64_setup():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008r2_64', regname)))
	
	for regname, reghive in hives.items():
		_, err = setup_test(reghive)
		assert err is None


def test_2008r2_64_fullwalk():
    hives = {}
    for regname in REGHIVE_NAMES:
        hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008r2_64', regname)))
    
    for regname, reghive in hives.items():
        _, err = setup_test(reghive)
        assert err is None

    for regname, reghive in hives.items():
        _, err = fullwalk_test(reghive)
        assert err is None


def test_2008r2_64_sam():
    samhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008r2_64', 'sam.reg')))
    _, err = setup_test(samhive)
    assert err is None
    _, err = sam_test(samhive)
    assert err is None


def test_2008r2_64_security():
	securityhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008r2_64', 'security.reg')))
	_, err = setup_test(securityhive)
	assert err is None
	_, err = security_test(securityhive)
	assert err is None


def test_2008r2_64_system():
	systemhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2008r2_64', 'system.reg')))
	_, err = setup_test(systemhive)
	assert err is None
	_, err = system_test(systemhive)
	assert err is None


def test_nt_setup():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('nt', regname)))
	
	for regname, reghive in hives.items():
		_, err = setup_test(reghive)
		assert err is None


def test_nt_fullwalk():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('nt', regname)))
	
	for regname, reghive in hives.items():
		_, err = setup_test(reghive)
		assert err is None

	for regname, reghive in hives.items():
		_, err = fullwalk_test(reghive)
		assert err is None


def test_nt_sam():
	samhive = AIOWinRegHive(open_file(REG_DIR.joinpath('nt', 'sam.reg')))
	_, err = setup_test(samhive)
	assert err is None
	_, err = sam_test(samhive)
	assert err is None


#def test_nt_security():
#	securityhive = AIOWinRegHive(open_file(REG_DIR.joinpath('nt', 'security.reg')))
#	_, err = setup_test(securityhive)
#	assert err is None
#	_, err = security_test(securityhive)
#	assert err is None
#
#
#def test_nt_system():
#	systemhive = AIOWinRegHive(open_file(REG_DIR.joinpath('nt', 'system.reg')))
#	_, err = setup_test(systemhive)
#	assert err is None
#	_, err = system_test(systemhive)
#	assert err is None


def test_win2016_64_setup():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2016_64', regname)))
	
	for regname, reghive in hives.items():
		_, err = setup_test(reghive)
		assert err is None


def test_win2016_64_fullwalk():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2016_64', regname)))
	
	for regname, reghive in hives.items():
		_, err = setup_test(reghive)
		assert err is None

	for regname, reghive in hives.items():
		_, err = fullwalk_test(reghive)
		assert err is None


def test_win2016_64_sam():
	samhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2016_64', 'sam.reg')))
	_, err = setup_test(samhive)
	assert err is None
	_, err = sam_test(samhive)
	assert err is None


def test_win2016_64_security():
	securityhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2016_64', 'security.reg')))
	_, err = setup_test(securityhive)
	assert err is None
	_, err = security_test(securityhive)
	assert err is None


def test_win2016_64_system():
	systemhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2016_64', 'system.reg')))
	_, err = setup_test(systemhive)
	assert err is None
	_, err = system_test(systemhive)
	assert err is None


def test_win2019_64_setup():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2019_64', regname)))
	
	for regname, reghive in hives.items():
		_, err = setup_test(reghive)
		assert err is None


def test_win2019_64_fullwalk():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2019_64', regname)))
	
	for regname, reghive in hives.items():
		_, err = setup_test(reghive)
		assert err is None

	for regname, reghive in hives.items():
		_, err = fullwalk_test(reghive)
		assert err is None


def test_win2019_64_sam():
	samhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2019_64', 'sam.reg')))
	_, err = setup_test(samhive)
	assert err is None
	_, err = sam_test(samhive)
	assert err is None


def test_win2019_64_security():
	securityhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2019_64', 'security.reg')))
	_, err = setup_test(securityhive)
	assert err is None
	_, err = security_test(securityhive)
	assert err is None


def test_win2019_64_system():
	systemhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2019_64', 'system.reg')))
	_, err = setup_test(systemhive)
	assert err is None
	_, err = system_test(systemhive)
	assert err is None


def test_win2022_64_setup():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2022_64', regname)))
	
	for regname, reghive in hives.items():
		_, err = setup_test(reghive)
		assert err is None


def test_win2022_64_fullwalk():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = AIOWinRegHive(open_file(REG_DIR.joinpath('win2022_64', regname)))
	
	for regname, reghive in hives.items():
		_, err = setup_test(reghive)
		assert err is None

	for regname, reghive in hives.items():
		_, err = fullwalk_test(reghive)
		assert err is None


def test_win2022_64_sam():
	samhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2022_64', 'sam.reg')))
	_, err = setup_test(samhive)
	assert err is None
	_, err = sam_test(samhive)
	assert err is None


def test_win2022_64_security():
	securityhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2022_64', 'security.reg')))
	_, err = setup_test(securityhive)
	assert err is None
	_, err = security_test(securityhive)
	assert err is None


def test_win2022_64_system():
	systemhive = AIOWinRegHive(open_file(REG_DIR.joinpath('win2022_64', 'system.reg')))
	_, err = setup_test(systemhive)
	assert err is None
	_, err = system_test(systemhive)
	assert err is None


if __name__ == '__main__':
	test_nt_setup()