# Volatility
# Copyright (C) 2007,2008 Volatile Systems
# Copyright (C) 2010,2011,2012 Michael Hale Ligh <michael.ligh@mnin.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

from volatility import obj
from volatility.plugins.windows import common
from volatility.plugins.windows.gui import win32k_core


class Sessions(common.WinProcessFilter):
    """List details on _MM_SESSION_SPACE (user logon sessions)"""

    __name = "sessions"

    def __init__(self, **kwargs):
        super(Sessions, self).__init__(**kwargs)
        self.profile = win32k_core.Win32GUIProfile(self.profile)

    def session_spaces(self):
        """Generates unique _MM_SESSION_SPACE objects.

        Generates unique _MM_SESSION_SPACE objects referenced by active
        processes.

        Yields:
          _MM_SESSION_SPACE instantiated from the session space's address space.
        """
        seen = []
        for proc in self.filter_processes():
            if proc.SessionId and proc.SessionId.v() not in seen:
                ps_ad = proc.get_process_address_space()
                if ps_ad:
                    seen.append(proc.SessionId.v())

                    yield self.profile._MM_SESSION_SPACE(
                        offset=proc.Session.v(), vm=ps_ad)

    def find_session_space(self, session_id):
        """ Get a _MM_SESSION_SPACE object by its ID.

        Args:
          session_id: the session ID to find.

        Returns:
          _MM_SESSION_SPACE instantiated from the session space's address space.
        """
        for session in self.session_spaces():
            if session.SessionId == session_id:
                return session

        return obj.NoneObject("Cannot locate a session %s", session_id)

    def render(self, renderer):
        # Use the modules plugin to resolve the module addresses.
        module_plugin = self.session.plugins.modules()

        for session in self.session_spaces():
            renderer.section()

            renderer.format("Session(V): {0:x} ID: {1} Processes: {2}\n",
                            session.obj_offset,
                            session.SessionId,
                            len(list(session.processes())))

            renderer.format("PagedPoolStart: {0:x} PagedPoolEnd {1:x}\n",
                            session.PagedPoolStart,
                            session.PagedPoolEnd)

            for process in session.processes():
                renderer.format(" Process: {0} {1} {2} @ {3:#x}\n",
                                process.UniqueProcessId,
                                process.ImageFileName,
                                process.CreateTime,
                                process)

            for image in session.images():
                module = module_plugin.find_module(image.Address)

                renderer.format(" Image: {0:#x}, Address {1:x}, Name: {2}\n",
                                image.obj_offset,
                                image.Address,
                                module.BaseDllName)
