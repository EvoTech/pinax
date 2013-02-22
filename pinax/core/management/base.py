from __future__ import absolute_import, unicode_literals
import optparse

import pinax



class CommandError(Exception):
    pass


class BaseCommand(object):
    """
    Stripped down version of Django's BaseCommand needed strictly for
    pinax-admin.
    """
    
    option_list = []
    help = ""
    args = ""
    
    def version(self):
        return pinax.__version__
    
    def usage(self, command):
        usage = "%%prog {0} [options] {1}".format(command, self.args)
        if self.help:
            return "{0}\n\n{1}".format(usage, self.help)
        else:
            return usage
    
    def create_parser(self, prog_name, command):
        return optparse.OptionParser(
            prog = prog_name,
            usage = self.usage(command),
            version = self.version(),
            option_list = self.option_list
        )
    
    def print_help(self, prog_name, command):
        parser = self.create_parser(prog_name, command)
        parser.print_help()
    
    def run_from_argv(self, argv):
        parser = self.create_parser(argv[0], argv[1])
        options, args = parser.parse_args(argv[2:])
        self.handle(*args, **options.__dict__)
