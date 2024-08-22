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

from ....utils.override import overrides
from ...boards.mem_mode import MemMode
from .pe_core import PECore

from ...processors.abstract_generator import AbstractGenerator
from ...boards.abstract_board import AbstractBoard

from typing import List

import numpy as np

class PETile(AbstractGenerator):
    def __init__(
        self,
        num_cores: int = 1,        
        block_size: int = 64,
        global_mem_size: np.uint64 = 0x2000000000,
        local_mem_offset: np.uint64 = 0x000000000,
        grid_width: np.uint64 = 4
    ) -> None:
        super().__init__(
            cores=self._create_cores(
                num_cores=num_cores,
                block_size=block_size,
                global_mem_size=global_mem_size,
                local_mem_offset = local_mem_offset,
                grid_width = grid_width
            )
        )
    
    def _create_cores(
        self,
        num_cores: int,
        block_size: int,
        global_mem_size: np.uint64 = 0x2000000000,
        local_mem_offset: np.uint64 = 0x000000000,
        grid_width: np.uint64 = 4
    ) -> List[PECore]:
        """
        The helper function to create the cores for the generator, it will use
        the same inputs as the constructor function.
        """
        return [
            PECore(
                block_size=block_size,
                global_mem_size=global_mem_size,
                local_mem_offset=local_mem_offset,
                grid_width=grid_width
            )
            for _ in range(num_cores)
        ]

    @overrides(AbstractGenerator)
    def start_traffic(self) -> None:
        """
        This function will start the assigned traffic to this generator.
        """
        for core in self.cores:
            core.start_traffic()

    def _parseTraffic(self, fpath: str = "../files/Traffic_Pattern/single-tile-test.json"):
        self.cores[0]._parseTraffic(fpath)