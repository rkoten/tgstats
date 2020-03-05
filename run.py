import sys
from os.path import isfile

from tgstats import *


if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = input('Enter exported json file path: ')

    if isfile(filename):
        tgstats = TgStats(filename)
        tgstats.compute()
        tgstats.render()
    else:
        print('Invalid path.')
