# Detailed Documentation for `sat.py` and `sat2.py`

This documentation provides a comprehensive overview of the modules `sat.py` and `sat2.py`, explaining their functionality, logic, and usage. These modules implement SAT formula verification and the reduction of SAT problems to Integer Linear Programming (ILP) for solving with the PULP library.

---

## **`sat.py`**

The `sat.py` module focuses on **verifying the correctness of a solution** to a SAT formula. It evaluates whether a given assignment satisfies a logical formula represented using custom data structures.

### **Key Components**

#### **Classes and Enums**
- **`Operator` Enum**:
  Represents the three logical operators used in SAT formulas:
  - `AND` (conjunction)
  - `OR` (disjunction)
  - `NOT` (negation)

- **`Set` Class**:
  - Models SAT formulas recursively.
  - Attributes:
    - `operator`: Specifies the logical operation (e.g., `AND`, `OR`, `NOT`).
    - `values`: A list of either:
      - Strings representing variable names (e.g., `'a'`, `'b'`).
      - Nested `Set` objects for complex expressions.

---

### **Functions**

#### **`verify_sat(equation: Set, input: dict[str, bool]) -> bool`**
- **Purpose**: 
  Validates if a given variable assignment satisfies the SAT formula.
- **Parameters**:
  - `equation`: A `Set` object representing the SAT formula.
  - `input`: A dictionary mapping variable names to boolean values (`True`/`False`).
- **Returns**:
  - `True` if the formula is satisfied by the assignment.
  - `False` otherwise.
  
- **Logic**:
  - If all `values` in the `Set` are strings, it applies the operator directly to the corresponding values from the `input`.
  - For nested structures, it recursively evaluates subexpressions.

#### **Helper Functions**
1. **`use_operator_on_values(equation: Set, input: dict[str, bool]) -> bool`**
   - Directly evaluates the SAT formula when it involves only variable names and no nested expressions.
   - E.g., `(a AND b)` checks if both `a` and `b` are `True` in `input`.

2. **`use_operator_on_booleans(operator: Operator, booleans: List[bool]) -> bool`**
   - Handles nested SAT formulas by applying logical operators to boolean results from subformulas.

---

### **Testing**
- The module contains extensive tests to validate `verify_sat`:
  - **Single-variable Tests**: Validate correctness of simple formulas like `NOT(a)`.
  - **Multi-variable Tests**: Test expressions like `(a OR b)` and `(a AND b)`.
  - **Nested Formulas**: Validate recursive evaluation for complex SAT problems.

---

## **`sat2.py`**

The `sat2.py` module implements the **reduction of SAT problems to Integer Linear Programming (ILP)** and solves them using the PULP library. The goal is to transform a SAT problem into a linear system of equations and use ILP solvers to find satisfying assignments.

### **Key Components**

#### **Classes and Enums**
- **`Operator` Enum**:
  Identical to `sat.py`, representing the three logical operators: `AND`, `OR`, `NOT`.

- **`Set` Class**:
  Same as in `sat.py`, used to represent SAT formulas recursively.

---

### **Functions**

#### **`sat_to_ilp(equation: Set) -> Tuple[LpProblem, Dict[str, LpVariable]]`**
- **Purpose**:
  Translates a SAT formula into an ILP problem.
- **Parameters**:
  - `equation`: A `Set` object representing the SAT formula.
- **Returns**:
  - An `LpProblem` object representing the ILP problem.
  - A dictionary mapping SAT variable names to their corresponding binary ILP variables.

- **Logic**:
  - Each SAT variable is mapped to a binary ILP variable (`0` or `1`).
  - Logical operators are modeled using linear constraints:
    - **NOT**: `NOT_A == 1 - A`
    - **OR**: 
      - `A_OR_B >= A`
      - `A_OR_B >= B`
      - `A_OR_B <= A + B`
    - **AND**: 
      - `A_AND_B <= A`
      - `A_AND_B <= B`
      - `A_AND_B >= A + B - 1`
  - A root auxiliary variable represents the entire formula, constrained to evaluate to `1` (True).

#### **`solve_ilp(equation: Set) -> Dict[str, bool]`**
- **Purpose**:
  Solves the ILP problem derived from the SAT formula.
- **Parameters**:
  - `equation`: A `Set` object representing the SAT formula.
- **Returns**:
  - A dictionary mapping variable names to boolean values for a satisfying assignment.
- **Behavior**:
  - Solves the ILP problem using PULP.
  - Returns the assignment if the problem is satisfiable.
  - Raises an exception if no solution exists.

---

### **Example**

**SAT Problem**: `NOT((a AND b) OR NOT(c))`

```python
from sat2 import solve_ilp, Set, Operator

# Define the SAT formula
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

# Solve the SAT formula via ILP
try:
    solution = solve_ilp(equation)
    print("SAT solution:", solution)
except Exception as e:
    print("No solution:", e)
```

Output:
```plaintext
SAT solution: {'a': False, 'b': False, 'c': True}
```

---

### **Testing**
The module includes extensive tests for:
1. **Simple Formulas**:
   - Single-variable problems like `a`, `NOT(a)`.
2. **Logical Operators**:
   - Tests for `AND`, `OR`, and `NOT`.
3. **Nested Formulas**:
   - Complex expressions combining multiple operators, e.g., `(a AND b) OR NOT(c)`.

---

## **Key Insights**

### **Differences Between `sat.py` and `sat2.py`**
1. **`sat.py`**:
   - Focuses on verifying solutions for a given SAT formula.
   - Uses recursion and boolean evaluation for verification.
   
2. **`sat2.py`**:
   - Converts SAT problems into ILP formulations.
   - Solves the problem using an ILP solver to find satisfying assignments.

### **Logical Modeling with ILP**
- **Why ILP?**:
  - Provides a standardized approach for solving logical constraints using linear equations.
- **Binary Variables**:
  - Represent boolean values (`0` for False, `1` for True).
- **Constraints**:
  - Encode logical operators using linear equations, enabling efficient computation with ILP solvers.

---

## **Conclusion**

The `sat.py` module provides tools to validate SAT solutions, while `sat2.py` demonstrates the reduction of SAT to ILP. Together, they illustrate the interplay between SAT problems and linear programming, showcasing how logical problems can be tackled using mathematical optimization techniques.