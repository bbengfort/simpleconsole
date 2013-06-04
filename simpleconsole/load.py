import os

from base import BaseCommand, CommandError

class FilePathCommand(BaseCommand):
    
    args  = "<path path ...>"
    label = "path"

    def check_path(self, path):
        try:
            with open(path, 'rb') as f: pass
            return True
        except IOError:
            return False

    def handle(self, *paths, **options):
        
        if not paths:
            raise CommandError("Provide at least one %s." % self.label)

        output = []
        for path in paths:

            if not self.check_path(path):
                output.append("%s is not a valid %s." % (path, self.label))
                continue

            path_output = self.handle_path(path, **options)
            if path_output:
                output.append(path_output)
        output.append("")
        return '\n'.join(output)

    def handle_path(self, path, **options):
        """
        Perform the command's actions for path.
        """
        raise NotImplementedError()
