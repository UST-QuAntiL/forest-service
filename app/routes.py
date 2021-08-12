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

from app import app, forest_handler, implementation_handler, db, parameters
from app.result_model import Result
from flask import jsonify, abort, request
import logging
import json
import base64
import re


@app.route('/forest-service/api/v1.0/transpile', methods=['POST'])
def transpile_circuit():
    """Get implementation from URL. Pass input into implementation. Generate and transpile circuit
    and return depth and width."""

    if not request.json or not 'qpu-name' in request.json:
        abort(400)

    qpu_name = request.json['qpu-name']
    impl_language = request.json.get('impl-language', '')
    input_params = request.json.get('input-params', "")
    impl_url = request.json.get('impl-url', "")
    bearer_token = request.json.get("bearer-token", "")
    input_params = parameters.ParameterDictionary(input_params)
    # adapt if real backends are available
    token = ''
    # if 'token' in input_params:
    #     token = input_params['token']
    # elif 'token' in request.json:
    #     token = request.json.get('token')
    # else:
    #     abort(400)

    if impl_url is not None and impl_url != "":
        impl_url = request.json['impl-url']
        if impl_language.lower() == 'quil':
            short_impl_name = 'no name'
            circuit = implementation_handler.prepare_code_from_quil_url(impl_url, bearer_token)
        else:
            short_impl_name = "untitled"
            try:
                circuit = implementation_handler.prepare_code_from_url(impl_url, input_params, bearer_token)
            except ValueError:
                abort(400)

    elif 'impl-data' in request.json:
        impl_data = base64.b64decode(request.json.get('impl-data').encode()).decode()
        short_impl_name = 'no short name'
        if impl_language.lower() == 'quil':
            circuit = implementation_handler.prepare_code_from_quil(impl_data)
        else:
            try:
                circuit = implementation_handler.prepare_code_from_data(impl_data, input_params)
            except ValueError:
                abort(400)
    else:
        abort(400)

    backend = forest_handler.get_qpu(token, qpu_name)
    if not backend:
        app.logger.warn(f"{qpu_name} not found.")
        abort(404)

    try:
        nq_program = backend.compiler.quil_to_native_quil(circuit, protoquil=True)
        transpiled_circuit = backend.compiler.native_quil_to_executable(nq_program)

        # count number of multi qubit gates
        program_string = transpiled_circuit.program
        multi_qubit_gates_regex = '(CZ|XY|CNOT|CCNOT|CPHASE00|CPHASE01|CPHASE10|CPHASE|SWAP|CSWAP|ISWAP|PSWAP)'
        number_of_multi_qubit_gates = len([*re.finditer(multi_qubit_gates_regex, program_string)])

        width = len(nq_program.get_qubits())
        # gate_depth: the longest subsequence of compiled instructions where adjacent instructions share resources
        depth = nq_program.native_quil_metadata.gate_depth
        # multi_qubit_gate_depth: Maximum number of successive two-qubit gates in the native quil program
        multi_qubit_gate_depth = nq_program.native_quil_metadata.multiqubit_gate_depth
        total_number_of_gates = nq_program.native_quil_metadata.gate_volume
        print(nq_program.native_quil_metadata)

    except Exception:
        app.logger.info(f"Transpile {short_impl_name} for {qpu_name}: too many qubits required")
        return jsonify({'error': 'too many qubits required'}), 200

    app.logger.info(f"Transpile {short_impl_name} for {qpu_name}: "
                    f"w={width}, "
                    f"d={depth}, "
                    f"total number of gates={total_number_of_gates}, "
                    f"number of multi qubit gates={number_of_multi_qubit_gates}, "
                    f"multi qubit gate depth={multi_qubit_gate_depth}")

    return jsonify({'depth': depth,
                    'multi-qubit-gate-depth': multi_qubit_gate_depth,
                    'width': width,
                    'number-of-gates': total_number_of_gates,
                    'number-of-multi-qubit-gates': number_of_multi_qubit_gates,
                    'transpiled-quil': transpiled_circuit.program}), 200


@app.route('/forest-service/api/v1.0/execute', methods=['POST'])
def execute_circuit():
    """Put execution job in queue. Return location of the later result."""
    if not request.json or not 'qpu-name' in request.json:
        abort(400)
    qpu_name = request.json['qpu-name']
    impl_language = request.json.get('impl-language', '')
    impl_url = request.json.get('impl-url')
    bearer_token = request.json.get("bearer-token", "")
    impl_data = request.json.get('impl-data')
    transpiled_quil = request.json.get('transpiled-quil')
    input_params = request.json.get('input-params', "")
    input_params = parameters.ParameterDictionary(input_params)
    shots = request.json.get('shots', 1024)
    if 'token' in input_params:
        token = input_params['token']
    elif 'token' in request.json:
        token = request.json.get('token')
    else:
        abort(400)

    job = app.execute_queue.enqueue('app.tasks.execute', impl_url=impl_url, impl_data=impl_data,
                                    impl_language=impl_language, transpiled_quil=transpiled_quil, qpu_name=qpu_name,
                                    token=token, input_params=input_params, shots=shots, bearer_token=bearer_token)
    result = Result(id=job.get_id())
    db.session.add(result)
    db.session.commit()

    logging.info('Returning HTTP response to client...')
    content_location = '/forest-service/api/v1.0/results/' + result.id
    response = jsonify({'Location': content_location})
    response.status_code = 202
    response.headers['Location'] = content_location
    return response


@app.route('/forest-service/api/v1.0/calculate-calibration-matrix', methods=['POST'])
def calculate_calibration_matrix():
    """Put calibration matrix calculation job in queue. Return location of the later result."""
    pass


@app.route('/forest-service/api/v1.0/results/<result_id>', methods=['GET'])
def get_result(result_id):
    """Return result when it is available."""
    result = Result.query.get(result_id)
    if result.complete:
        result_dict = json.loads(result.result)
        return jsonify({'id': result.id, 'complete': result.complete, 'result': result_dict}), 200
    else:
        return jsonify({'id': result.id, 'complete': result.complete}), 200


@app.route('/forest-service/api/v1.0/version', methods=['GET'])
def version():
    return jsonify({'version': '1.0'})
