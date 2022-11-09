from unittest import TestCase

from pyquil import Program
from pyquil.gates import MEASURE, H, CNOT

from app.analysis import get_non_transpiled_circuit_metrics


def circuit1() -> Program:
	p = Program()
	ro = p.declare('ro', 'BIT', 2)
	p += H(0)
	p += H(0)
	p += H(1)

	for i in range(ro.declared_size):
		p += MEASURE(i, ro[i])

	return p


def circuit2() -> Program:
	p = Program()
	ro = p.declare('ro', 'BIT', 2)
	p += H(0)
	p += H(0)
	p += H(0)
	p += H(0)
	p += CNOT(0, 1)
	p += H(1)

	for i in range(ro.declared_size):
		p += MEASURE(i, ro[i])

	return p


def circuit3() -> Program:
	p = Program()
	ro = p.declare('ro', 'BIT', 3)
	p += H(0)
	p += CNOT(0, 1)
	p += H(0)
	p += H(1)
	p += CNOT(1, 2)

	for i in range(ro.declared_size):
		p += MEASURE(i, ro[i])

	return p


class TestNonTranspiledMetrics(TestCase):
	def test_circuit1(self):
		self.assertDictEqual(
			get_non_transpiled_circuit_metrics(circuit1()),
			{
				'original-depth': 2,
				'original-multi-qubit-gate-depth': 0,
				'original-width': 2,
				'original-total-number-of-operations': 5,
				'original-number-of-multi-qubit-gates': 0,
				'original-number-of-measurement-operations': 2,
				'original-number-of-single-qubit-gates': 3,
			}
		)

	def test_circuit2(self):
		self.assertDictEqual(
			get_non_transpiled_circuit_metrics(circuit2()),
			{
				'original-depth': 6,
				'original-multi-qubit-gate-depth': 1,
				'original-width': 2,
				'original-total-number-of-operations': 8,
				'original-number-of-multi-qubit-gates': 1,
				'original-number-of-measurement-operations': 2,
				'original-number-of-single-qubit-gates': 5,
			}
		)

	def test_circuit3(self):
		self.assertDictEqual(
			get_non_transpiled_circuit_metrics(circuit3()),
			{
				'original-depth': 4,
				'original-multi-qubit-gate-depth': 2,
				'original-width': 3,
				'original-total-number-of-operations': 8,
				'original-number-of-multi-qubit-gates': 2,
				'original-number-of-measurement-operations': 3,
				'original-number-of-single-qubit-gates': 3,
			}
		)
