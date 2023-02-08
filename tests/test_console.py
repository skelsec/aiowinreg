from aiowinreg.examples.console import WinRegReaderConsole
import pathlib
import pytest
import asyncio

CURRENT_FILE_PATH = pathlib.Path(__file__).parent.absolute()
REG_DIR = CURRENT_FILE_PATH.joinpath('testdata')
REGHIVE_NAMES = ['sam.reg', 'security.reg', 'system.reg', 'software.reg']

@pytest.mark.asyncio
async def test_load():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole()
		_, err = await console.do_open(regpath)
		assert err is None

@pytest.mark.asyncio
async def test_load_on_init():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None

@pytest.mark.asyncio
async def test_ls():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None
		_, err = await console.do_ls()
		assert err is None

@pytest.mark.asyncio
async def test_lsval():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None
		_, err = await console.do_lsval()
		assert err is None

@pytest.mark.asyncio
async def test_class():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None
		_, err = await console.do_class()
		assert err is None

@pytest.mark.asyncio
async def test_sd():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None
		_, err = await console.do_sd()
		assert err is None

@pytest.mark.asyncio
async def test_cd():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None
		_, err = await console.do_cd('')
		assert err is None

@pytest.mark.asyncio
async def test_walk():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None
		_, err = await console.do_walk(3)
		assert err is None

@pytest.mark.asyncio
async def test_cat_sam():
	samhive = REG_DIR.joinpath('win2022_64', 'sam.reg')
	console = WinRegReaderConsole(samhive)
	_, err = await console.do_open()
	assert err is None
	_, err = await console.do_cd('SAM\\Domains\\Account\\Users')
	assert err is None
	_, err = await console.do_lsval()
	assert err is None
	res, err = await console.do_cat('default')
	assert err is None
	assert res is True

@pytest.mark.asyncio
async def test_cd_completitions():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None
		console._cd_completions()

@pytest.mark.asyncio
async def test_cat_completitions():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None
		console._cat_completions()

@pytest.mark.asyncio
async def test_get_currentkeys():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None
		console.get_current_keys()

@pytest.mark.asyncio
async def test_get_currentkeys():
	hives = {}
	for regname in REGHIVE_NAMES:
		hives[regname] = REG_DIR.joinpath('win2022_64', regname)
	
	for regname, regpath in hives.items():
		console = WinRegReaderConsole(regpath)
		_, err = await console.do_open()
		assert err is None
		console.get_current_vals()

@pytest.mark.asyncio
async def test_wrong_file():
	console = WinRegReaderConsole('not_a_file.reg')
	_, err = await console.do_open()
	assert err is not None

@pytest.mark.asyncio
async def test_wrong_cat_val():
	samhive = REG_DIR.joinpath('win2022_64', 'sam.reg')
	console = WinRegReaderConsole(samhive)
	_, err = await console.do_open()
	assert err is None
	_, err = await console.do_cd('SAM\\Domains\\Account\\Users')
	assert err is None
	_, err = await console.do_lsval()
	assert err is None
	res, err = await console.do_cat('default1')
	assert err is not None
	assert res is False

if __name__ == '__main__':
	asyncio.run(test_cat_sam())