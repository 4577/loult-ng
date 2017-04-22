from asyncio import create_subprocess_shell
from asyncio.subprocess import PIPE


class BanFail(Exception):

    state = None

    def __init__(self, state):
        super().__init__()
        self.state = state


class Ban:

    ban_types = ('ban', 'slowban')
    commands = {
        'apply': 'ipset add "{ban_type}" "{ip}" timeout "{timeout}"',
        'remove': 'ipset del "{ban_type}" "{ip}"',
        'add_set': 'ipset create "{ban_type}" hash:net timeout 0',
    }

    def __init__(self, ban_type, state, timeout=0):
        try:
            self.timeout = int(timeout)
        except TypeError:
            raise BanFail('timeout_wrong_type')
        if self.timeout < 0:
            raise BanFail('timeout_invalid')
        if state not in self.commands:
            raise BanFail('wrong_state')
        if ban_type not in self.ban_types:
            raise BanFail('wrong_type')

        self.type = ban_type
        self.state = state
        self.template = self.commands[state]

    @classmethod
    async def ensure_sets(cls):
        for ip_set in cls.ban_types:
            cmd = cls.commands['add_set'].format(ban_type=ip_set)
            err = await cls._run_cmd(cmd)
            if cls._is_fatal(err):
                raise BanFail('Failed to ensure the needed IP sets exist.')

    def __call__(self, ip_list):
        return self._ban(ip_list)

    async def _ban(self, ip_list):
        if len(ip_list) == 0:
            raise BanFail('wrong_userid')

        for ip in ip_list:
            err = await self._run_cmd(self._make_cmd(ip))
            if self._is_fatal(err):
                await self._handle_failure(ip_list)

        return self.state + '_ok'

    def _make_cmd(self, ip):
        return self.template.format(timeout=self.timeout,
                                    ban_type=self.type, ip=ip)

    @staticmethod
    async def _run_cmd(cmd):
        process = await create_subprocess_shell(cmd, stderr=PIPE)
        code = await process.wait()
        stderr = await process.stderr.readline()
        if code == 0:
            return None
        else:
            return stderr.decode('utf-8').rstrip(" \n")

    @staticmethod
    def _is_fatal(err):
       return err is not None and not (
              err.endswith("it's not added") or
              err.endswith("it's already added") or
              err.endswith("set with the same name already exists"))

    async def _handle_failure(self, ip_list):
        """Removes all bans that we tried to set."""
        if self.state == 'apply':
            try:
                ban = Ban(self.type, 'remove')
                await ban(ip_list)
            except BanFail:
                raise BanFail('backend_failure')
        raise BanFail(self.state + '_fail')
