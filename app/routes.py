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
from pyquil import get_qc

from app import app, forest_handler, implementation_handler, db, parameters
from app.generated_circuit_model import Generated_Circuit
from app.result_model import Result
from app.analysis import get_circuit_metrics, get_non_transpiled_circuit_metrics
from flask import jsonify, abort, request
import logging
import json
import base64


@app.route('/forest-service/api/v1.0/generate-circuit', methods=['POST'])
def generate_circuit():
    if not request.json:
        abort(400)

    impl_language = request.json.get('impl-language', '')
    impl_url = request.json.get('impl-url', "")
    input_params = request.json.get('input-params', "")
    bearer_token = request.json.get("bearer-token", "")
    impl_data = ''
    if input_params:
        input_params = parameters.ParameterDictionary(input_params)

    if impl_url is not None and impl_url != "":
        impl_url = request.json['impl-url']
    elif 'impl-data' in request.json:
        impl_data = base64.b64decode(request.json.get('impl-data').encode()).decode()
    else:
        abort(400)

    job = app.implementation_queue.enqueue('app.tasks.generate', impl_url=impl_url, impl_data=impl_data,
                                           impl_language=impl_language, input_params=input_params,
                                           bearer_token=bearer_token)

    result = Generated_Circuit(id=job.get_id())
    db.session.add(result)
    db.session.commit()

    app.logger.info('Returning HTTP response to client...')
    content_location = '/forest-service/api/v1.0/generated-circuits/' + result.id
    response = jsonify({'Location': content_location})
    response.status_code = 202
    response.headers['Location'] = content_location
    response.autocorrect_location_header = True
    return response


@app.route('/forest-service/api/v1.0/generated-circuits/<generated_circuit_id>', methods=['GET'])
def get_generated_circuit(generated_circuit_id):
    """Return result when it is available."""
    generated_circuit = Generated_Circuit.query.get(generated_circuit_id)
    if generated_circuit.complete:
        input_params_dict = json.loads(generated_circuit.input_params)
        return jsonify(
            {'id': generated_circuit.id, 'complete': generated_circuit.complete, 'input_params': input_params_dict,
             'generated-circuit': generated_circuit.generated_circuit,
             'original-depth': generated_circuit.original_depth, 'original-width': generated_circuit.original_width,
             'original-total-number-of-operations': generated_circuit.original_total_number_of_operations,
             'original-number-of-multi-qubit-gates': generated_circuit.original_number_of_multi_qubit_gates,
             'original-number-of-measurement-operations': generated_circuit.original_number_of_measurement_operations,
             'original-number-of-single-qubit-gates': generated_circuit.original_number_of_single_qubit_gates,
             'original-multi-qubit-gate-depth': generated_circuit.original_multi_qubit_gate_depth}), 200
    else:
        return jsonify({'id': generated_circuit.id, 'complete': generated_circuit.complete}), 200


@app.route('/forest-service/api/v1.0/analyze-original-circuit', methods=['POST'])
def analyze_original_circuit():
    impl_language = request.json.get('impl-language', '')
    input_params = request.json.get('input-params', {'token': ''})
    impl_url = request.json.get('impl-url', "")
    bearer_token = request.json.get("bearer-token", "")

    if impl_url is not None and impl_url != "":
        impl_url = request.json['impl-url']
        if impl_language.lower() == 'quil':
            circuit = implementation_handler.prepare_code_from_quil_url(impl_url, bearer_token)
        else:
            try:
                circuit = implementation_handler.prepare_code_from_url(impl_url, input_params, bearer_token)
            except ValueError:
                abort(400)

    elif 'impl-data' in request.json:
        impl_data = base64.b64decode(request.json.get('impl-data').encode()).decode()
        if impl_language.lower() == 'quil':
            circuit = implementation_handler.prepare_code_from_quil(impl_data)
        else:
            try:
                circuit = implementation_handler.prepare_code_from_data(impl_data, input_params)
            except ValueError:
                abort(400)
    else:
        abort(400)

    try:
        metrics = get_non_transpiled_circuit_metrics(circuit)

    except Exception:
        return jsonify({'error': 'analysis failed'}), 200

    return jsonify(metrics), 200


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
    metrics = get_circuit_metrics(circuit, backend, short_impl_name, qpu_name)


    return jsonify(metrics), 200


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
    correlation_id = request.json.get('correlation-id', None)
    if 'token' in input_params:
        token = input_params['token']
    elif 'token' in request.json:
        token = request.json.get('token')
    else:
        abort(400)

    job = app.execute_queue.enqueue('app.tasks.execute', correlation_id=correlation_id, impl_url=impl_url, impl_data=impl_data,
                                    impl_language=impl_language, transpiled_quil=transpiled_quil, qpu_name=qpu_name,
                                    token=token, input_params=input_params, shots=shots, bearer_token=bearer_token)
    result = Result(id=job.get_id(), backend=qpu_name, shots=shots)
    db.session.add(result)
    db.session.commit()

    logging.info('Returning HTTP response to client...')
    content_location = '/forest-service/api/v1.0/results/' + result.id
    response = jsonify({'Location': content_location})
    response.status_code = 202
    response.headers['Location'] = content_location
    response.autocorrect_location_header = True
    return response


@app.route('/forest-service/api/v1.0/results/<result_id>', methods=['GET'])
def get_result(result_id):
    """Return result when it is available."""
    result = Result.query.get(result_id)
    if result.complete:
        result_dict = json.loads(result.result)
        if result.post_processing_result:
            post_processing_result_dict = json.loads(result.post_processing_result)
            return jsonify(
                {'id': result.id, 'complete': result.complete, 'result': result_dict, 'backend': result.backend,
                 'shots': result.shots, 'generated-circuit-id': result.generated_circuit_id,
                 'post-processing-result': post_processing_result_dict}), 200
        else:
            return jsonify(
                {'id': result.id, 'complete': result.complete, 'result': result_dict, 'backend': result.backend,
                 'shots': result.shots}), 200
    else:
        return jsonify({'id': result.id, 'complete': result.complete}), 200


@app.route('/forest-service/api/v1.0/version', methods=['GET'])
def version():
    return jsonify({'version': '1.0'})
