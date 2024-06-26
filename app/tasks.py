# ******************************************************************************
#  Copyright (c) 2021 University of Stuttgart
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

from app import implementation_handler, forest_handler, db, app
from rq import get_current_job

from pyquil import Program

from app.analysis import get_non_transpiled_circuit_metrics
from app.generated_circuit_model import Generated_Circuit
from app.result_model import Result
import logging
import json
import base64


def generate(impl_url, impl_data, impl_language, input_params, bearer_token):
    app.logger.info("Starting generate task...")
    job = get_current_job()

    generated_circuit_code = None
    if impl_url:
        if impl_language.lower() == 'quil':
            generated_circuit_code = implementation_handler.prepare_code_from_quil_url(impl_url, bearer_token)
        else:
            generated_circuit_code = implementation_handler.prepare_code_from_url(impl_url, input_params, bearer_token)
    elif impl_data:
        impl_data = base64.b64decode(impl_data.encode()).decode()
        if impl_language.lower() == 'quil':
            generated_circuit_code = implementation_handler.prepare_code_from_quil(impl_data)
        else:
            generated_circuit_code = implementation_handler.prepare_code_from_data(impl_data, input_params)
    else:
        generated_circuit_object = Generated_Circuit.query.get(job.get_id())
        generated_circuit_object.generated_circuit = json.dumps({'error': 'generating circuit failed'})
        generated_circuit_object.complete = True
        db.session.commit()

    if generated_circuit_code:

        metrics = get_non_transpiled_circuit_metrics(generated_circuit_code)

        generated_circuit_object = Generated_Circuit.query.get(job.get_id())
        generated_circuit_object.generated_circuit = generated_circuit_code.out()

        generated_circuit_object.original_depth = metrics['original-depth']
        generated_circuit_object.original_width = metrics['original-width']
        generated_circuit_object.original_total_number_of_operations = metrics['original-total-number-of-operations']
        generated_circuit_object.original_number_of_multi_qubit_gates = metrics['original-number-of-multi-qubit-gates']
        generated_circuit_object.original_number_of_measurement_operations = metrics['original-number-of-measurement-operations']
        generated_circuit_object.original_number_of_single_qubit_gates = metrics['original-number-of-single-qubit-gates']
        generated_circuit_object.original_multi_qubit_gate_depth = metrics['original-multi-qubit-gate-depth']

        generated_circuit_object.input_params = json.dumps(input_params)
        app.logger.info(f"Received input params for circuit generation: {generated_circuit_object.input_params}")
        generated_circuit_object.complete = True
        db.session.commit()


def execute(correlation_id, impl_url, impl_data, impl_language, transpiled_quil, input_params, token, qpu_name, shots, bearer_token: str):
    """Create database entry for result. Get implementation code, prepare it, and execute it. Save result in db"""
    job = get_current_job()

    backend = forest_handler.get_qpu(token, qpu_name)
    if not backend:
        result = Result.query.get(job.get_id())
        result.result = json.dumps({'error': 'qpu-name or token wrong'})
        result.complete = True
        db.session.commit()

    logging.info('Preparing implementation...')
    circuit = None
    if transpiled_quil:
        circuit = Program(transpiled_quil)
    else:
        if impl_url and not correlation_id:
            if impl_language.lower() == 'quil':
                circuit = implementation_handler.prepare_code_from_quil_url(impl_url, bearer_token)
            else:
                circuit = implementation_handler.prepare_code_from_url(impl_url, input_params, bearer_token)
        elif impl_data:
            impl_data = base64.b64decode(impl_data.encode()).decode()
            if impl_language.lower() == 'quil':
                circuit = implementation_handler.prepare_code_from_quil(impl_data)
            else:
                circuit = implementation_handler.prepare_code_from_data(impl_data, input_params)
    if not circuit:
        result = Result.query.get(job.get_id())
        result.result = json.dumps({'error': 'URL not found'})
        result.complete = True
        db.session.commit()

    logging.info('Start transpiling...')
    try:
        circuit.wrap_in_numshots_loop(shots=shots)

        if not transpiled_quil:
            nq_program = backend.compiler.quil_to_native_quil(circuit, protoquil=True)
        else:
            nq_program = circuit

        transpiled_circuit = backend.compiler.native_quil_to_executable(nq_program)
    except Exception:
        result = Result.query.get(job.get_id())
        result.result = json.dumps({'error': 'too many qubits required'})
        result.complete = True
        db.session.commit()

    logging.info('Start executing...')
    job_result = forest_handler.execute_job(transpiled_circuit, shots, backend)
    if job_result:
        result = Result.query.get(job.get_id())
        result.result = json.dumps(job_result)
        # check if implementation contains post processing of execution results that has to be executed
        if correlation_id and (impl_url or impl_data):
            result.generated_circuit_id = correlation_id
            # prepare input data containing execution results and initial input params for generating the circuit
            generated_circuit = Generated_Circuit.query.get(correlation_id)
            input_params_for_post_processing = json.loads(generated_circuit.input_params)
            input_params_for_post_processing['counts'] = json.loads(result.result)

            if impl_url:
                post_p_result = implementation_handler.prepare_code_from_url(url=impl_url[0],
                                                                             input_params=input_params_for_post_processing,
                                                                             bearer_token=bearer_token,
                                                                             post_processing=True)
            elif impl_data:
                post_p_result = implementation_handler.prepare_post_processing_code_from_data(data=impl_data[0],
                                                                                              input_params=input_params_for_post_processing)
            result.post_processing_result = json.loads(post_p_result)
        result.complete = True
        db.session.commit()
    else:
        result = Result.query.get(job.get_id())
        result.result = json.dumps({'error': 'execution failed'})
        result.complete = True
        db.session.commit()
