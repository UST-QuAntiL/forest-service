# ******************************************************************************
#  Copyright (c) 2022 University of Stuttgart
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

from typing import Dict

from pyquil import Program
from pyquil.api import QuantumComputer
from pyquil.device import Qubit
from pyquil.quilbase import Measurement, Gate

from app import app
import re

multi_qubit_gates_regex = '(CZ|XY|CNOT|CCNOT|CPHASE00|CPHASE01|CPHASE10|CPHASE|SWAP|CSWAP|ISWAP|PSWAP)'
measurement_operations_regex = 'MEASURE'


def get_circuit_depth(circuit: Program):
    depths: Dict[Qubit, int] = {}

    for qubit in circuit.get_qubits(False):
        depths[qubit] = 0

    for instruction in circuit.instructions[1:]:
        if isinstance(instruction, Measurement):
            continue

        if hasattr(instruction, 'qubits'):
            if len(instruction.qubits) == 1:
                for qubit in instruction.qubits:
                    depths[qubit] += 1
            else:
                max_depth_of_effected_qubits = 0

                for qubit in instruction.qubits:
                    max_depth_of_effected_qubits = max(max_depth_of_effected_qubits, depths[qubit])

                for qubit in instruction.qubits:
                    depths[qubit] = max_depth_of_effected_qubits + 1
        else:
            raise KeyError(f"Instruction {instruction} has no attribute named 'qubits'")

    return max(depths.values())


def remove_single_qubit_gates(circuit: Program) -> Program:
    multi_qubit_circuit = circuit.copy_everything_except_instructions()

    for inst in circuit.instructions:
        if isinstance(inst, Gate):
            if len(inst.qubits) > 1:
                multi_qubit_circuit.inst(inst)
        else:
            multi_qubit_circuit.inst(inst)

    return multi_qubit_circuit


def get_number_of_multi_qubit_gates(circuit: Program) -> int:
    multi_qubit_gates = 0

    for inst in circuit.instructions:
        if hasattr(inst, "qubits"):
            if len(inst.qubits) > 1:
                multi_qubit_gates += 1

    return multi_qubit_gates


def get_number_of_measurement_operations(circuit: Program) -> int:
    number_of_measurement_operations = 0

    for inst in circuit.instructions:
        if isinstance(inst, Measurement):
            number_of_measurement_operations += 1

    return number_of_measurement_operations


def get_non_transpiled_circuit_metrics(non_transpiled_circuit: Program) -> Dict:
    number_of_multi_qubit_gates = get_number_of_multi_qubit_gates(non_transpiled_circuit)
    number_of_measurement_operations = get_number_of_measurement_operations(non_transpiled_circuit)
    width = len(non_transpiled_circuit.get_qubits())

    # analyze depth of original circuit
    depth = get_circuit_depth(non_transpiled_circuit)

    # multi_qubit_gate_depth: Maximum number of successive two-qubit gates in the native quil program
    multi_qubit_circuit = remove_single_qubit_gates(non_transpiled_circuit)
    multi_qubit_gate_depth = get_circuit_depth(multi_qubit_circuit)

    # total number of gates for non-transpiled circuit
    total_number_of_gates = 0
    for instruction in non_transpiled_circuit.instructions[1:]:
        if hasattr(instruction, 'qubits'):
            total_number_of_gates += 1

    number_of_single_qubit_gates = total_number_of_gates\
        - number_of_multi_qubit_gates

    total_number_of_operations = total_number_of_gates \
        + number_of_measurement_operations

    return {
        'original-depth': depth,
        'original-multi-qubit-gate-depth': multi_qubit_gate_depth,
        'original-width': width,
        'original-total-number-of-operations': total_number_of_operations,
        'original-number-of-multi-qubit-gates': number_of_multi_qubit_gates,
        'original-number-of-measurement-operations': number_of_measurement_operations,
        'original-number-of-single-qubit-gates': number_of_single_qubit_gates,
    }


def get_circuit_metrics(circuit: Program, backend: QuantumComputer, short_impl_name: str, qpu_name: str) -> Dict:
    non_transpiled_circuit = circuit
    nq_program = backend.compiler.quil_to_native_quil(circuit, protoquil=True)
    transpiled_circuit = backend.compiler.native_quil_to_executable(nq_program)

    # count number of multi qubit gates
    program_string = transpiled_circuit.program
    number_of_multi_qubit_gates = len([*re.finditer(multi_qubit_gates_regex, program_string)])

    # count number of measurement operations
    program_string = transpiled_circuit.program
    print(transpiled_circuit.program)
    number_of_measurement_operations = len([*re.finditer(measurement_operations_regex, program_string)])
    width = len(nq_program.get_qubits())

    # gate_depth: the longest subsequence of compiled instructions where adjacent instructions share resources
    depth = nq_program.native_quil_metadata.gate_depth

    # multi_qubit_gate_depth: Maximum number of successive two-qubit gates in the native quil program
    multi_qubit_gate_depth = nq_program.native_quil_metadata.multiqubit_gate_depth
    total_number_of_gates = nq_program.native_quil_metadata.gate_volume

    # count number of single qubit gates
    number_of_single_qubit_gates = total_number_of_gates - number_of_multi_qubit_gates

    # count total number of all operations including gates and measurement operations
    total_number_of_operations = total_number_of_gates + number_of_measurement_operations

    print(nq_program.native_quil_metadata)

    app.logger.info(
        f"Transpile {short_impl_name} for {qpu_name}: "
        f"w={width}, "
        f"d={depth}, "
        f"total number of operations={total_number_of_operations}, "
        f"number of single qubit gates={number_of_single_qubit_gates}, "
        f"number of multi qubit gates={number_of_multi_qubit_gates}, "
        f"number of measurement operations={number_of_measurement_operations}, "
        f"multi qubit gate depth={multi_qubit_gate_depth}")

    circuit_metrics = {
        'depth': depth,
        'multi-qubit-gate-depth': multi_qubit_gate_depth,
        'width': width,
        'total-number-of-operations': total_number_of_operations,
        'number-of-single-qubit-gates': number_of_single_qubit_gates,
        'number-of-multi-qubit-gates': number_of_multi_qubit_gates,
        'number-of-measurement-operations': number_of_measurement_operations,
        'transpiled-quil': transpiled_circuit.program
    }

    circuit_metrics.update(get_non_transpiled_circuit_metrics(non_transpiled_circuit))

    return circuit_metrics
