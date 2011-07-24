#!/usr/bin/python -tt
#
# Copyright (c) 2009-2010, Adam Simpkins
#
import re
import socket
import sys

from . import err
from . import util

FREEDB_SERVER = 'freedb.freedb.org'
DEFAULT_SERVER = FREEDB_SERVER


class MatchResponse(object):
    def __init__(self, category, disc_id, title):
        self.category = category
        self.discId = disc_id
        self.title = title

    def __repr__(self):
        return ('MatchResponse(%r, %#x, %r)' %
                (self.category, self.discId, self.title))

    def __str__(self):
        return '(%s, %#x, %r)' % (self.category, self.discId, self.title)


class Connection(object):
    def __init__(self, server, port=8880):
        self.__readbuf = ''
        self.debug = False

        self.server = server
        self.port = port
        addr = (self.server, port)
        self.conn = socket.create_connection(addr, timeout=30)
        self.conn.settimeout(30)

        self.__login()

    def __login(self):
        # Read the server status line
        (code, line) = self.readResponse()
        if code != 200 and code != 201:
            raise err.ProtocolError('server %s:%s responded with unexpected '
                                    'initial response code %d: %r' %
                                    (self.server, self.port, code, line))

        #m = re.match('^(.*) CDDBP server (.*) ready at (.*)$', line)
        #if not m:
        #    raise err.ProtocolError('unexpected status line from CDDB server '
        #                            '%s:%s: %r' %
        #                            (self.server, self.port, line))
        #hostname = m.group(1)
        #version = m.group(2)
        #date = m.group(3)

        # Send the hello command
        username = 'anonymous'
        hostname = 'example.com'
        client = 'amass'
        version = '0.1'
        hello_cmd = ('cddb hello %s %s %s %s' %
                     (username, hostname, client, version))
        self.sendCommand(hello_cmd)

        # Receive the hello response
        (code, line) = self.readResponse()
        if code != 200 and code != 201:
            raise err.ProtocolError('server %s:%s rejected hello request with '
                                    'code %d: %r' %
                                    (self.server, self.port, code, line))

        # Send the proto command to set the CDDB protocol level
        self.sendCommand('proto 6')
        (code, line) = self.readResponse()
        if code != 201 and code != 502:
            if code == 501:
                # TODO: We could send just a plain "proto" command
                # to figure out the highest level supported by the server,
                # just for diagnostic purposes.
                raise err.ProtocolError('server %s:%s does not support '
                                        'protocol level 6' %
                                        (self.server, self.port))
            else:
                raise err.ProtocolError('server %s:%s rejected attempt to use '
                                        'protocol level 6: %d %r' %
                                        (self.server, self.port, code, line))

    def query(self, toc):
        disc_id = util.get_cddb_id(toc)
        track_offsets = ' '.join([str(o) for o in util.get_track_offsets(toc)])
        end_seconds = util.get_disc_length(toc)
        cmd = ('cddb query %x %s %s %s' %
               (disc_id, len(toc.tracks), track_offsets, end_seconds))
        self.sendCommand(cmd)

        (code, line) = self.readResponse()
        if code == 200:
            # one entry, in line
            matches = [line]
        elif code == 210:
            # multiple entries on following lines
            matches = self.readUntilDot()
        elif code == 211 or code == 202:
            # No match found
            return []
        else:
            raise err.ProtocolError('server %s:%s responded with unexpected '
                                    'query response code %d: %r' %
                                    (self.server, self.port, code, line))

        responses = []
        for match in matches:
            try:
                (category, id_str, title) = match.split(' ', 2)
            except ValueError:
                err.ProtocolError('server %s:%s returned unexpected query '
                                  'response: %r' % (match,))
            try:
                id = int(id_str, 16)
            except ValueError:
                err.ProtocolError('server %s:%s returned unexpected disc ID '
                                  '%r in query response: %r' % (id_str, match))
            responses.append(MatchResponse(category, id, title))

        return responses

    def read(self, category, disc_id):
        cmd = 'cddb read %s %x' % (category, disc_id)
        self.sendCommand(cmd)

        (code, line) = self.readResponse()
        if code == 401:
            raise err.NoMatchesError(disc_id, category)
        elif code != 210:
            raise err.ProtocolError('server %s:%s responded with unexpected '
                                    'read response code %d: %r' %
                                    (self.server, self.port, code, line))

        # If we're still here, we got a 210 response
        lines = self.readUntilDot()
        buf = '\n'.join(lines)
        if buf:
            buf += '\n'
        return buf

    def debugMsg(self, msg):
        if self.debug:
            print >> sys.stderr, msg

    def sendCommand(self, cmd):
        # Encode Unicode strings as UTF-8.
        if isinstance(cmd, unicode):
            cmd = cmd.encode('UTF-8')

        self.debugMsg('sending: %r' % (cmd,))
        self.conn.send(cmd + '\r\n')

    def readline(self):
        # We could be more efficient about this and avoid so much
        # buffer copying, but this is simple and sufficient for now
        while True:
            idx = self.__readbuf.find('\r\n')
            if idx > 0:
                line = self.__readbuf[:idx]
                self.__readbuf = self.__readbuf[idx+2:]
                # Decode as UTF-8 before returning.
                # (It's okay to do our line processing on the binary data,
                # since the line terminator is still '\r\n'.  In fact, it would
                # be incorrect to try and decode it as UTF-8 first, since we
                # might have read a partial character at the end.)
                return line.decode('UTF-8')

            readsize = 4096
            (buf, addr) = self.conn.recvfrom(readsize)
            self.debugMsg('read: %r' % (buf,))
            self.__readbuf += buf

    def readResponse(self):
        line = self.readline()
        try:
            (code_str, rest) = line.split(' ', 1)
            code = int(code_str)
        except ValueError:
            raise err.ProtocolError('unexpected response from CDDB server '
                                    '%s:%s: %r' %
                                    (self.server, self.port, line))

        return (code, rest)

    def readUntilDot(self):
        lines = []
        while True:
            line = self.readline()
            if line == '.':
                return lines
            lines.append(line)


def query_cddb(toc, server=DEFAULT_SERVER):
    """
    Query CDDB for information about the specified disc.

    Returns a map of { category_name : buffer }, where the buffer contains
    the raw CDDB data for that category.

    This is just a convenience wrapper around Connection.query() and
    Connection.read().
    """
    # Connect to the server, and query for matching discs
    conn = Connection('freedb.freedb.org')
    matches = conn.query(toc)

    # Read the data for each match
    results = {}
    for match in matches:
        results[match.category] = conn.read(match.category, match.discId)

    return results
