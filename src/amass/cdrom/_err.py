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
