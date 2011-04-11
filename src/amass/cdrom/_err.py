#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
class CdError(Exception):
    pass

class NoCdTextError(CdError):
    def __init__(self, device):
        CdError.__init__(self, 'media in %s does not contain CD-TEXT' %
                         (device,))
        self.device = device

class CdTextNotSupportedError(CdError):
    def __init__(self, device):
        CdError.__init__(self, 'drive %s does not support CD-TEXT' %
                         (device,))
        self.device = device

class CdTextError(CdError):
    pass

class NoDiscError(CdError):
    def __init__(self, device):
        CdError.__init__(self, 'no disc in drive %s' % (device,))
        self.device = device

class TrayOpenError(CdError):
    def __init__(self, device):
        CdError.__init__(self, '%s: tray is open' % (device,))
        self.device = device

class DriveNotReadyError(CdError):
    def __init__(self, device):
        CdError.__init__(self, 'drive %s is not ready' % (device,))
        self.device = device
