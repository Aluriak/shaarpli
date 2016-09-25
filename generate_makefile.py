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

    # serve
    command = 'uwsgi --socket 127.0.0.1:{} --wsgi-file shaarpli/shaarpli.py'
    recipes['serve'] = {command.format(
        userstring('UWSGI port', default=3031),
    )}

    # ssh
    if userbool('upload through ssh ?', default=True):
        upload_command = 'scp -r -P {port} ./$OUTPUT_FILES {user}@{host}:{path}'
        retrieve_command = 'scp -r -P {port} {user}@{host}:{path}/$OUTPUT_FILES ./'
                    #mv shaarpli/ old_shaarpli/
                        scp -r -P 9834 lucas@163.172.222.20:~/dev_www/shaarpli/{shaarpli.py,shaarpli,data} ./

        params = {
            'host': userstring('hostname (IP or domain)', default='127.0.0.1'),
            'port': userint('port', default=22),
            'user': userstring('user', default=getpass.getuser()),
            'path': userstring('path', default='~/shaarpli'),
        }
        recipes['upload'] = {upload_command.format(**params)}
        recipes['retrieve'] = {
            'mkdir -p old_shaarpli/',
            'mv $OUTPUT_FILES old_shaarpli/',
            retrieve_command.format(**params),
        }
        constants = {
            'OUTPUT_FILES={{shaarpli.py,shaarpli}}'
        }


    # write the Makefile
    makefile = user_choose_makefile()
    if makefile:
        with open(makefile, 'w') as fd:
            fd.write('\n'.join(constants))
            for recipe, commands in recipes.items():
                fd.write('{}:\n'.format(recipe))
                fd.write('\t' + '\n\t'.join(commands) + '\n')
            print(makefile, 'have been written')
