from __future__ import annotations
from pulp import LpVariable, LpProblem, LpMaximize, LpStatus
from typing import List, Union, Tuple
from pydantic import BaseModel
from enum import Enum
import unittest

# Objects we use to define 'equations' / 'gates' -------------------------------
class Operator(Enum):
  AND = 0
  OR = 1
  NOT = 2


class Set(BaseModel):
  operator: Operator
  values: List[Union[str, Set]] # If the operator is 'NOT' there is only a list of one element

# Reduction from SAT -> ILP ---------------------------------------
def sat_to_ilp(equation: Set) -> Tuple[LpProblem, dict[str, LpVariable]]:
    problem = LpProblem("SAT_to_ILP", LpMaximize)

    variables = {}

    
    aux_counter = {"count": 0}

    def generate_aux_var():
        aux_name = f"aux_{aux_counter['count']}"
        aux_counter["count"] += 1
        return LpVariable(aux_name, 0, 1, cat="Binary")

    def process_set(equation: Union[Set, str]) -> LpVariable:
        nonlocal problem  

        if isinstance(equation, str):
            if equation not in variables:
                variables[equation] = LpVariable(f"x_{equation}", 0, 1, cat="Binary")
            return variables[equation]

        op = equation.operator
        values = [process_set(v) for v in equation.values]

        aux_var = generate_aux_var()

        if op == Operator.AND:
            for v in values:
                problem += aux_var <= v
            problem += aux_var >= sum(values) - len(values) + 1

        elif op == Operator.OR:
            for v in values:
                problem += aux_var >= v
            problem += aux_var <= sum(values)

        elif op == Operator.NOT:
            problem += aux_var == 1 - values[0]

        return aux_var

    root = process_set(equation)

    problem += root, "Satisfiability"

    return problem, variables


# Validator --------------------------------------------------
def verify_sat(equation: Set, input: dict[str, bool]) -> bool:
  if all(isinstance(v, str) for v in equation.values):
    return use_operator_on_values(equation, input)
  else:
    return use_operator_on_booleans(equation.operator, [verify_sat(v, input) for v in equation.values])

# Helper methods ---------------------
def solve_ilp(equation: Set) -> dict[str, bool]:
    problem, variables = sat_to_ilp(equation)

    problem.solve()

    if LpStatus[problem.status] == "Optimal":
        return {var_name: bool(round(var.value())) for var_name, var in variables.items()}
    else:
        raise Exception("No solution")
    
def use_operator_on_values(equation: Set, input: dict[str, bool]) -> bool:
  if equation.operator == Operator.NOT:
    # if len(equation.values) != 1:
    # raise Exception
    return not input[equation.values[0]]
  if equation.operator == Operator.AND:
    return all(input[v] for v in equation.values)
  if equation.operator == Operator.OR:
    return any(input[v] for v in equation.values)
  raise ValueError("Unknown operator")

def use_operator_on_booleans(operator: Operator, booleans: List[bool]) -> bool:
  if operator == Operator.NOT:
    # if len(booleans) != 1:
    # raise Exception
    return not booleans[0]
  if operator == Operator.AND:
    return all(booleans)
  if operator == Operator.OR:
    return any(booleans)
  raise ValueError("Unknown operator")

# Tests for actual
class TestSatToILP(unittest.TestCase):

    def test_single_variable(self):
        equation = Set(operator=Operator.OR, values=["a"])
        solution = solve_ilp(equation)
        self.assertTrue(solution["a"])

    def test_not_operator(self):
        equation = Set(operator=Operator.NOT, values=["a"])
        solution = solve_ilp(equation)
        self.assertFalse(solution["a"]) 

    def test_and_operator(self):
        equation = Set(operator=Operator.AND, values=["a", "b"])
        solution = solve_ilp(equation)
        self.assertTrue(solution["a"])
        self.assertTrue(solution["b"])

    def test_or_operator(self):
        equation = Set(operator=Operator.OR, values=["a", "b"])
        solution = solve_ilp(equation)
        self.assertTrue(any(solution.values()))  

    def test_nested_and_or(self):
        equation = Set(
            operator=Operator.OR,
            values=[
                Set(operator=Operator.AND, values=["a", "b"]),
                "c"
            ],
        )
        solution = solve_ilp(equation)
        self.assertTrue(any(solution.values())) 

    def test_complex_nested_expression(self):
        equation = Set(
            operator=Operator.NOT,
            values=[
                Set(
                    operator=Operator.OR,
                    values=[
                        Set(operator=Operator.AND, values=["a", "b"]),
                        Set(operator=Operator.NOT, values=["c"]),
                    ],
                )
            ],
        )
        solution = solve_ilp(equation)
        self.assertFalse(solution["a"] and solution["b"]) 
        self.assertTrue(solution["c"])

# Validator tets Simple sets ---------------------------------------------------
def test_single_and_true():
  set = Set(operator=Operator.AND, values=['a'])
  input = {'a': True}
  sol = verify_sat(set, input=input)
  assert sol

def test_single_or_true():
  set = Set(operator=Operator.OR, values=['a'])
  input = {'a': True}
  sol = verify_sat(set, input=input)
  assert sol

def test_single_not_true():
  set = Set(operator=Operator.NOT, values=['a'])
  input = {'a': False}
  sol = verify_sat(set, input=input)
  assert sol

def test_single_not_false():
  set = Set(operator=Operator.NOT, values=['a'])
  input = {'a': True}
  sol = verify_sat(set, input=input)
  assert not sol

def test_double_or_true():
  set = Set(operator=Operator.OR, values=['a', 'b'])
  input = {'a': True, 'b': False}
  sol = verify_sat(set, input=input)
  assert sol

def test_double_and_true():
  set = Set(operator=Operator.AND, values=['a', 'b'])
  input = {'a': True, 'b': True}
  sol = verify_sat(set, input=input)
  assert sol

def test_double_or_false():
  set = Set(operator=Operator.OR, values=['a', 'b'])
  input = {'a': False, 'b': False}
  sol = verify_sat(set, input=input)
  assert not sol

def test_double_and_false():
  set = Set(operator=Operator.AND, values=['a', 'b'])
  input = {'a': True, 'b': False}
  sol = verify_sat(set, input=input)
  assert not sol

def test_double_and_false():
  set = Set(operator=Operator.AND, values=['a', 'b'])
  input = {'a': False, 'b': False}
  sol = verify_sat(set, input=input)
  assert not sol

# Validator tests Set of sets ---------------------------------------
def test_not_set():
  sub_set1 = Set(operator=Operator.AND, values=['a', 'b'])
  set = Set(operator=Operator.NOT, values=[sub_set1])
  input = {'a': False, 'b': False}
  sol = verify_sat(set, input=input)
  assert sol

def test_not_set_sets():
  sub_set1 = Set(operator=Operator.AND, values=['a', 'b'])
  sub_set2 = Set(operator=Operator.AND, values=['a', 'b'])
  sub_set3 = Set(operator=Operator.AND, values=[sub_set1, sub_set2])
  set = Set(operator=Operator.NOT, values=[sub_set3])
  input = {'a': True, 'b': True}
  sol = verify_sat(set, input=input)
  assert not sol