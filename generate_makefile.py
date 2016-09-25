"""Helper for Makefile generation"""


import os
import getpass
from collections import OrderedDict


def userbool(prompt:str, default:bool=None) -> bool or default:
    accept_default = default is not None
    prompt += ' [{}/{}]'.format('Y' if default is True else 'y',
                                'N' if default is False else 'n')
    correct = lambda s: any(s.startswith(l) for l in 'yYnN') or (accept_default and s.strip() == '')
    answer = 'invalid'
    while not correct(answer):
        answer = input(prompt)
    return default if (accept_default and answer == '') else (answer.lower() == 'y')


def userint(prompt:str, default:int=None) -> int or default:
    accept_default = default is not None
    prompt += ' [{}]'.format(default) if accept_default else ''
    correct = lambda s: answer.isnumeric() or (accept_default and s.strip() == '')
    answer = 'invalid'
    while not correct(answer):
        answer = input(prompt)
    return default if accept_default and not answer else int(answer)


def userstring(prompt, default:str=None) -> str or default:
    accept_default = default is not None
    prompt += ' [{}]'.format(default) if accept_default else ''
    answer = input(prompt)
    return default if accept_default and not answer else answer


def user_choose_makefile(names:iter=('makefile', 'Makefile', 'makefile.f')) -> str:
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
    constants = []  # iterable of constants printed at the Makefile beginning

    # serve
    constants += [
        'UWSGI_URL=' + userstring('UWSGI server url ?', default='127.0.0.1'),
        'UWSGI_PORT=' + str(userint('UWSGI port ?', default='3031')),
    ]
    recipes['serve'] = (
        'uwsgi --socket $(UWSGI_URL):$(UWSGI_PORT) --wsgi-file shaarpli/shaarpli.py',
    )

    # ssh
    if userbool('upload through ssh ?', default=True):
        upload_command = 'scp -r -P $(PORT) ./$(FILES) $(USER)@$(HOST):$(REMOTE_PATH)'
        retrieve_command = 'scp -r -P $(PORT) $(USER)@$(HOST):$(REMOTE_PATH)/$(FILES) ./'

        recipes['upload'] = (
            upload_command,
        )
        recipes['retrieve'] = (
            'mkdir -p old_shaarpli/',
            '- mv $(OUTPUT_FILES) old_shaarpli/',
            retrieve_command,
        )
        constants += [
            'FILES={shaarpli.py,shaarpli}',
            'HOST=' + userstring('hostname (IP or domain)', default='127.0.0.1'),
            'PORT=' + str(userint('port', default=22)),
            'USER=' + userstring('user', default=getpass.getuser()),
            'REMOTE_PATH=' + userstring('path', default='~/shaarpli'),
        ]


    # write the Makefile
    makefile = user_choose_makefile()
    if makefile:
        with open(makefile, 'w') as fd:
            fd.write('\n'.join(constants) + '\n\n')
            for recipe, commands in recipes.items():
                fd.write('{}:\n'.format(recipe))
                fd.write('\t' + '\n\t'.join(commands) + '\n')
            print(makefile, 'have been written')
