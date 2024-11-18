from pulp import LpVariable, LpProblem, LpMaximize, LpStatus
from typing import Dict, Tuple
from enum import Enum
from pydantic import BaseModel
from typing import List, Union


class Operator(Enum):
    AND = 0
    OR = 1
    NOT = 2


class Set(BaseModel):
    operator: Operator
    values: List[Union[str, "Set"]] 


def sat_to_ilp(equation: Set) -> Tuple[LpProblem, Dict[str, LpVariable]]:
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


def solve_ilp(equation: Set) -> Dict[str, bool]:
    problem, variables = sat_to_ilp(equation)

    problem.solve()

    if LpStatus[problem.status] == "Optimal":
        return {var_name: bool(round(var.value())) for var_name, var in variables.items()}
    else:
        raise Exception("No solution")


# Example SAT problem
if __name__ == "__main__":
    # NOT((a AND b) OR NOT c)
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

    try:
        solution = solve_ilp(equation)
        print("SAT solution:", solution)
    except Exception as e:
        print("Error:", e)

import unittest
from pulp import LpVariable
from typing import Dict
from pydantic import BaseModel
from enum import Enum




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



if __name__ == "__main__":
    unittest.main()
