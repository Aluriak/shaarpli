"""Helper for Makefile generation"""


import os
import getpass
from collections import OrderedDict


def userbool(prompt:str, default:bool=None) -> bool or default:
    accept_default = default is not None
    prompt += ' [{}/{}]'.format('Y' if default is True else 'y',
                                'N' if default is False else 'n')
    correct = lambda s: any(s.startswith(l) for l in 'yYnN') or (accept_default and s == '')
    answer = 'invalid'
    while not correct(answer):
        answer = input(prompt)
    return default if (accept_default and answer == '') else (answer.lower() == 'y')


def userint(prompt:str, default:int=None) -> int:
    accept_default = default is not None
    prompt += ' [{}]'.format(default) if accept_default else ''
    correct = lambda s: answer.isnumeric() or (accept_default and s == '')
    answer = 'invalid'
    while not correct(answer):
        answer = input(prompt)
    return default if accept_default and not answer else int(answer)


def userstring(prompt, default:str=None) -> str:
    accept_default = default is not None
    prompt += ' [{}]'.format(default) if accept_default else ''
    answer = input(prompt)
    return default if accept_default and not answer else answer


def user_choose_makefile(names:iter=('Makefile', 'makefile', 'makefile.f')) -> str:
    makefile = None
    for name in names:
        if os.path.exists(name):
            if userbool('Override existing {} ?'.format(name), default=False):
                makefile = name
                break
        else:
            makefile = name
            break
    return makefile


if __name__ == "__main__":
    recipes = OrderedDict()  # {recipe name: {commands}}
    if userbool('upload through ssh ?', default=True):
        command = 'scp -P {port} shaarcli/* {user}@{host}:{path}'
        recipes['upload'] = {command.format(
            host=userstring('hostname (IP or domain)', default='127.0.0.1'),
            port=userint('port', default=22),
            user=userstring('user', default=getpass.getuser()),
            path=userstring('path', default='~/shaarpli'),
        )}


    # write the Makefile
    makefile = user_choose_makefile()
    if makefile:
        with open(makefile, 'w') as fd:
            for recipe, commands in recipes.items():
                fd.write('{}:\n'.format(recipe))
                fd.write('\t' + '\n\t'.join(commands) + '\n')
            print(makefile, 'have been written')
