![Supported Python versions](https://img.shields.io/badge/python-3.7+-blue.svg) [![Twitter](https://img.shields.io/twitter/follow/skelsec?label=skelsec&style=social)](https://twitter.com/intent/follow?screen_name=skelsec)

## :triangular_flag_on_post: Sponsors

If you like this project, consider purchasing licenses of [OctoPwn](https://octopwn.com/), our full pentesting suite that runs in your browser!  
For notifications on new builds/releases and other info, hop on to our [Discord](https://discord.gg/PM8utcNxMS)

# aiowinreg
Registry hive reader library implementing both async and regural parsing

## :triangular_flag_on_post: Runs in the browser

This project, alongside with many other pentester tools runs in the browser with the power of OctoPwn!  
Check out the community version at [OctoPwn - Live](https://live.octopwn.com/)

# Installing
## Via pypi

`pip install aiowinreg`

## Via git + pip
```
git clone https://github.com/skelsec/aiowinreg
cd aiowinreg
pip install .
```
# Usage
This module is intended to be used as a library, however installing it provides a command line tool `awinreg` which can be used to traverse/read Windows hive files

# Tests
Tests are included in the `./test` folder with sample files from various Windows Server registry hives.
