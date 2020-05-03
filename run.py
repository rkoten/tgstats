import sys
from os.path import isfile, expanduser

from tgstats import *


if __name__ == '__main__':
    try:
        path = sys.argv[1]
    except IndexError:
        path = input('Enter exported json file path: ')

    path = expanduser(path)
    if isfile(path):
        tgstats = TgStats(path)
        tgstats.compute()
        tgstats.render()
    else:
        print('Invalid path.')
