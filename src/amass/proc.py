#!/usr/bin/python -tt

import fcntl
import os
import pipes
import select
import signal
import subprocess
import time
import types
import sys


PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT


class CmdError(Exception):
    def __init__(self, cmd):
        if isinstance(cmd, Proc):
            self.cmd = cmd.args
        else:
            self.cmd = cmd

    def getCmdString(self):
        if isinstance(self.cmd, (tuple, list)):
            return ' '.join([pipes.quote(arg) for arg in self.cmd])
        return str(self.cmd)

class CmdFailedError(CmdError):
    pass

class CmdStatusError(CmdFailedError):
    def __init__(self, cmd, status, expected_rc=None):
        CmdFailedError.__init__(self, cmd)
        self.status = status
        self.expectedStatus = expected_rc

    def __str__(self):
        return ('command %r exited with status %s' %
                (self.getCmdString(), self.status))


class CmdTerminatedError(CmdFailedError):
    def __init__(self, cmd, signum, expected_sig=None):
        CmdFailedError.__init__(self, cmd)
        self.signum = signum
        self.expectedSignals = expected_sig

    def __str__(self):
        return ('command %r was terminated with signal %s' %
                (self.getCmdString(), self.signum))


def run_cmd_any(cmd, stdin='/dev/null', stdout=PIPE, stderr=PIPE,
                cwd=None, env=None):
    """
    Like run_cmd(), but don't raise an exception, regardless of the
    exit code or termination signal.
    """
    # If stdin is a string, open that file to use as the child's stdin
    close_stdin = False
    if isinstance(stdin, types.StringTypes):
        stdin = os.open(stdin, os.O_RDONLY)
        close_stdin = True
    # We don't allow stdout or stderr to be strings, since
    # it is less clear if we should overwrite or append, plus permissions
    # for new files, etc.

    try:
        p = subprocess.Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr,
                             cwd=cwd, env=env)
    finally:
        if close_stdin:
            os.close(stdin)
    (cmd_out, cmd_err) = p.communicate()
    status = p.wait()

    return (status, cmd_out, cmd_err)


def run_cmd(cmd, stdin='/dev/null', stdout=PIPE, stderr=PIPE,
            cwd=None, env=None, expected_rc=(0), expected_sig=()):
    """
    Run a command, and collect the output printed on it's stdout and stderr.

    The exit status is checked against the expected_rc and expected_sig
    arguments.  If the exit status does not match one of these values, a
    CmdStatusError or CmdTerminatedError will be raised.
    """
    (status, cmd_out, cmd_err) = run_cmd_any(cmd, stdin=stdin, stdout=stdout,
                                             stderr=stderr, cwd=cwd, env=env)
    check_status(cmd, status, expected_rc, expected_sig)
    return (status, cmd_out, cmd_err)


def check_status(cmd, status, expected_rc=(0), expected_sig=()):
    """
    Check a command's exit status against a list of expected exit codes and
    signals.
    """
    if status >= 0 and expected_rc != None:
        if isinstance(expected_rc, (list, tuple)):
            expected_rc_list = expected_rc
        else:
            expected_rc_list = [expected_rc]
        if not status in expected_rc_list:
            raise CmdStatusError(cmd, status, expected_rc)
    if status < 0 and expected_sig != None:
        signum = -status
        if isinstance(expected_sig, (list, tuple)):
            expected_sig_list = expected_sig
        else:
            expected_sig_list = [expected_sig]
        if not signum in expected_sig_list:
            raise CmdTerminatedError(cmd, signum, expected_sig)


class Proc(subprocess.Popen):
    """
    Proc is a wrapper around subprocess.Popen.

    In addition to the normal subprocess.Popen features, it provides:

    - Support for simultaneously reading from the command's stdout and stderr,
      and return as soon as some data is available (rather than waiting until
      the process exits).
    - Support for reliably killing the process.
    - Support to performing a wait with a timeout.
    """
    def __init__(self, args, executable=None, stdin=None,
                 stdout=None, stderr=None, preexec_fn=None, close_fds=False,
                 shell=False, cwd=None, env=None):
        self.args = args

        # If stdin is a string, open that file to use as the child's stdin
        close_stdin = False
        if isinstance(stdin, types.StringTypes):
            stdin = os.open(stdin, os.O_RDONLY)
            close_stdin = True
        # We don't allow stdout or stderr to be strings, since
        # it is less clear if we should overwrite or append, plus permissions
        # for new files, etc.

        try:
            subprocess.Popen.__init__(self, args, executable=executable,
                                      stdin=stdin, stdout=stdout,
                                      stderr=stderr,
                                      preexec_fn=preexec_fn,
                                      close_fds=close_fds,
                                      shell=shell, cwd=cwd, env=env)
        finally:
            if close_stdin:
                os.close(stdin)

        # Put our stdout and stderr pipes (if any) in non-blocking mode
        if self.stdout:
            flags = fcntl.fcntl(self.stdout.fileno(), fcntl.F_GETFL)
            flags |= os.O_NONBLOCK
            fcntl.fcntl(self.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            self.stdoutEOF = False
        else:
            self.stdoutEOF = True

        if self.stderr:
            flags = fcntl.fcntl(self.stderr.fileno(), fcntl.F_GETFL)
            flags |= os.O_NONBLOCK
            fcntl.fcntl(self.stderr.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            self.stderrEOF = False
        else:
            self.stderrEOF = True

    def closePipes(self):
        if self.stdin is not None:
            self.stdin.close()
            self.stdin = None
        if self.stdout is not None:
            self.stdout.close()
            self.stdout = None
        if self.stderr is not None:
            self.stderr.close()
            self.stderr = None

    def read(self, timeout=None, bufsize=4096):
        """
        Read from the process' stdout and stderr.  Blocks until data is
        available on either stdout or stderr.  Once data is available, a tuple
        is returned consisting of the data read on stdout, and the data read on
        stderr.

        If stdout is not available (e.g., it was not opened as a pipe when the
        process was started), or if the write end of the pipe has been closed by
        the child process, None will be returned in the first entry of tuple.
        If data becomes available on stderr before any data is ready on stdout,
        '' will be returned in the first entry of the tuple.  The return value
        for stderr behaves the same way, respective to the stderr pipe.
        """
        read_fds = []
        if self.stdout is not None and not self.stdoutEOF:
            read_fds.append(self.stdout.fileno())
        if self.stderr is not None and not self.stderrEOF:
            read_fds.append(self.stderr.fileno())
        if not read_fds:
            return (None, None)

        (read_ready, ignore, ignore) = select.select(read_fds, [], [], timeout)

        if self.stdoutEOF:
            stdout_buf = None
        elif self.stdout.fileno() in read_ready:
            stdout_buf = os.read(self.stdout.fileno(), bufsize)
            if not stdout_buf:
                self.stdoutEOF = True
                stdout_buf = None
                # Close stdout now, so our pipe will get closed
                # even if we don't get garbage collected for a while
                self.stdout.close()
                self.stdout = None
        else:
            stdout_buf = ''

        if self.stderrEOF:
            stderr_buf = None
        elif self.stderr.fileno() in read_ready:
            stderr_buf = os.read(self.stderr.fileno(), bufsize)
            if not stderr_buf:
                self.stderrEOF = True
                stderr_buf = None
                # Close stderr now, so our pipe will get closed
                # even if we don't get garbage collected for a while
                self.stderr.close()
                self.stderr = None
        else:
            stderr_buf = ''

        return (stdout_buf, stderr_buf)

    def kill(self, sigterm_timeout=5, sigkill_timeout=None):
        """
        Try to kill the process, and wait for it to exit.
        """
        if self.returncode is not None:
            # Not running
            return

        # Send a SIGTERM
        os.kill(self.pid, signal.SIGTERM)
        # Wait for the process to exit
        retcode = self.wait(timeout=sigterm_timeout)
        if retcode is not None:
            return retcode

        # Hmm. The child still hasn't exited.  It's either ignoring our SIGTERM,
        # or it's cleanup code is taking too long to finish.
        # Try a SIGKILL next.
        #
        # XXX: Should we consider sending another SIGTERM before sending
        # SIGKILL?
        #
        # XXX: We might also want to consider looping and sending multiple
        # SIGKILLs.  If SIGKILL doesn't work, it most likely means the process
        # is stuck in a system call that won't return for some reason.  (e.g.,
        # hung non-interruptable NFS hard mount, or a kernel bug)
        os.kill(self.pid, signal.SIGKILL)
        return self.wait(timeout=sigkill_timeout)

    def wait(self, timeout=None, poll_interval=0.1):
        """
        Wait for the process to exit.

        Returns the negated signal number if the process was terminated by a
        signal, a non-negative integer if the process exited successfully.
        Returns None if the timeout expired before the process exited.

        If timeout is None, or is less than 0, this function will wait forever
        for the process to exit.  Otherwise, 
        """
        # If the process has already been successfully waited on,
        # return the stored return code.
        if self.returncode is not None:
            return self.returncode

        # If the timeout is infinite, use the standard subprocess wait()
        if timeout is None or timeout < 0:
            return subprocess.Popen.wait(self)

        time_left = timeout
        while True:
            # Call waitpid
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid != 0:
                # Excellent.  The child exited.
                self._handle_exitstatus(status)
                return self.returncode

            # If we have no time left, exit
            if time_left <= 0:
                return None

            time.sleep(poll_interval)
            time_left -= poll_interval
