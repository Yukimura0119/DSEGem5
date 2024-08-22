# Copyright (c) 2021 The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from m5.ticks import fromSeconds
from m5.util.convert import toLatency, toMemoryBandwidth
from m5.objects import PE, Port

from ..abstract_core import AbstractCore
from ..abstract_generator_core import AbstractGeneratorCore

from ....utils.override import overrides

import numpy as np

class PECore(AbstractGeneratorCore):
    def __init__(
        self,
        block_size: int = 64,
        global_mem_size: np.uint64 = 0x2000000000,
        local_mem_offset: np.uint64 = 0x000000000,
        grid_width: np.uint64 = 4
    ) -> None:
        super().__init__()
        self.generator = PE(block_size=block_size, global_mem_size=global_mem_size, local_mem_offset=local_mem_offset, grid_width=grid_width)
        self._block_size = block_size
        self._global_mem_size = global_mem_size
        self._local_mem_offset = local_mem_offset

    @overrides(AbstractCore)
    def connect_dcache(self, port: Port) -> None:
        self.generator.port = port

    @overrides(AbstractGeneratorCore)
    def start_traffic(self) -> None:
        self.generator.start()
    
    def _parseTraffic(self, fpath: str = "../files/Traffic_Pattern/traffic_pattern.json"):
        self.generator.parseTraffic(fpath)
