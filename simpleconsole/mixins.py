import os

from base import CommandError

class ConfirmationMixin(object):
    """
    Provides a confirmation method to a command class.

    Use C{confirm()} to have a command prompt with confirmation prompt the
    user in some way to fork execution of the command.
    """

    def confirm(self, prompt="Are you sure?", default=False):
        """
        Prompt the user for a yes/no answer.

        @param prompt: The text to prompt the user for the answer
        @param default: The expected default answer
        
        @return: The user's confirmation or cancelling of the prompt.
        @rtype: C{bool}
        """

        fmt = (prompt, "yes", "no") if default else (prompt, "no", "yes")
        prompt = "%s (%s|%s): " % fmt

        while True:
            ans = raw_input(prompt).lower()

            if ans == "yes":
                return True
            elif ans == "no":
                return False
            else:
                print "Please answer yes or no."

class OverwriteConfirmationMixin(ConfirmationMixin):
    """
    Checks if a supplied path exists, and if it does, prompts the user for
    confirmation about whether or not to overwrite the file, then deletes 
    the file for data integrity if yes, exits if not.

    Use C{confirm_overwrite()} to have the user confirm file overwrite.
    """

    def confirm_overwrite(self, path, force=False):
        """
        Supply a path to this method and it will check for the existence
        (not the writeability!) of a file at the path. If so, it will 
        prompt the user if they want to overwrite that file or not.

        @param path: The path to check whether or not to overwrite
        @param force: If true, warns the user of the overwrite, then does
        it anyway
        """
        if os.path.isfile(path):
            print self.style.WARNING("File exists at %s!" % path)
            if not force:
                if not super(OverwriteConfirmationMixin, self).confirm("Overwrite the file and permenantly destroy its contents?"):
                    raise CommandError("Unable to write to file at %s" % path)
            os.remove(path)
        return True

class WriteOutMixin(object):
    """
    Provide a helper function to write out to a path instead of stdout, or
    stdout otherwise. The path is checked to ensure no overwriting. Also,
    it checks an option value. 
    """

    def write(self, path=None, output=[]):
        
        if path is not None:
            with open(path, 'w') as out:
                out.write('\n'.join(output))

        else:
            if hasattr(self, 'stdout'):
                self.stdout.write('\n'.join(output))
