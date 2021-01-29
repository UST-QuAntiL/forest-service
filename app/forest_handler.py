# ******************************************************************************
#  Copyright (c) 2020 University of Stuttgart
#
#  See the NOTICE file(s) distributed with this work for additional
#  information regarding copyright ownership.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ******************************************************************************
from time import sleep

from pyquil import get_qc
from pyquil.api import local_forest_runtime, ForestConnection
import numpy as np
import os

# Get environment variables
qvm_hostname = os.environ.get('QVM_HOSTNAME', default='localhost')
qvm_port = os.environ.get('QVM_PORT', default=5666)
quilc_hostname = os.environ.get('QUILC_HOSTNAME', default= 'localhost')
quilc_port = os.environ.get('QVM_PORT', default=5667)

def get_qpu(token, qpu_name):
    """Get backend."""

    # Create a connection to the forest SDK
    connection = ForestConnection(
        sync_endpoint=f"http://{qvm_hostname}:{qvm_port}",
        compiler_endpoint=f"tcp://{quilc_hostname}:{quilc_port}")

    # Get Quantum computer as Quantum Virtual Machine
    return get_qc(name=qpu_name,
                  as_qvm=True,
                  connection=connection)



def delete_token():
    """Delete account."""
    pass


def execute_job(transpiled_circuit, shots, backend):
    """Genereate qObject from transpiled circuit and execute it. Return result."""

    stats = backend.run(transpiled_circuit)
    width = stats.shape[-1]

    def binary_string(x):
        return np.binary_repr(np.packbits(x, bitorder='little')[0], width=width)


    unique, counts = np.unique(stats, return_counts=True, axis=0)
    stats = dict(zip(map(binary_string, unique), map(int,counts)))
    print(stats)
    return stats
