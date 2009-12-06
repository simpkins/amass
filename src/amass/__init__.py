#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import logging


class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# Add an empty handler to the top-level logger.
# This way it won't warn about no handlers being configured
# Applications can add their own handlers if desired
log = logging.getLogger('amass')
log.setLevel(logging.WARNING)
log.addHandler(NullHandler())
