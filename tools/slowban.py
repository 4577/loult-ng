from asyncio import get_event_loop, create_subprocess_shell, gather
from itertools import product

# Add iptables to /etc/sudoers so bans can be automatically handled as
# the user the server runs as (unless it's running as root, but I hope
# you're not doing such a thing). To edit sudoers, run "visudo". If you're
# not fond of the "vi" editor, run instead, if you prefer, say, nano,
# "EDITOR=nano visudo", or "sudo EDITOR=nano visudo".
# Then add this line, replacing <user> with the user the server runs as:
# <user> ALL=(ALL) ALL, NOPASSWD: /sbin/iptables
# If you made a mistake, visudo will tell you and ask you to correct it,
# which you should do unless you want to break sudo AND *root login*.

commands = [
        'sudo iptables -I  INPUT -m statistic --mode random --probability 0.90 -s "{ip}" -j DROP',
        'sudo iptables -I OUTPUT -m statistic --mode random --probability 0.90 -s "{ip}" -j DROP',
    ]

del_commands = [cmd.replace(" -I ", " -D ") for cmd in commands]


class SlowbanFail(Exception):

    state = None

    def __init__(self, state):
        super().__init__()
        self.state = state


async def slowban(ip_list, state):
    if len(ip_list) == 0:
        raise SlowbanFail('wrong_userid')
    elif state == 'apply':
        cmds = commands
    elif state == 'remove':
        cmds = del_commands
    else:
        raise SlowbanFail('wrong_command')

    for ip, cmd_tpl in product(ip_list, cmds):
        cmd = cmd_tpl.format(ip=ip)
        process = await create_subprocess_shell(cmd)
        code = await process.wait()
        if code != 0:
            if state == 'apply':
                try:
                    await slowban(ip_list, 'remove')
                except SlowbanFail:
                    pass
            raise SlowbanFail(state + '_fail')

    return state + '_ok'
