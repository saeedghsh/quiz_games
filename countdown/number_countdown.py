"""Countdown numbers game."""

import ast
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import random
import select
import sys
import time
from typing import DefaultDict, Dict, List, Optional, Sequence, Set, Tuple

BIG_NUMBERS = (25, 50, 75, 100)
SMALL_NUMBERS = tuple(range(1, 10))
SMALL_NUMBER_REPEAT_LIMIT = 2
SMALL_NUMBER_POOL = tuple(
    number
    for number in SMALL_NUMBERS
    for _ in range(SMALL_NUMBER_REPEAT_LIMIT)
)
NUMBER_COUNT = 6
MIN_BIG_NUMBER_COUNT = 0
MAX_BIG_NUMBER_COUNT = 4
MIN_TARGET = 100
MAX_TARGET = 999
DEFAULT_SOLVER_TIME_LIMIT_SECONDS = 30
MAX_SOLUTIONS_TO_PRINT = 2


@dataclass(frozen=True)
class NumberRound:
    numbers: Tuple[int, ...]
    target: int


@dataclass(frozen=True)
class ExpressionEvaluation:
    is_valid: bool
    value: Optional[int]
    error: str = ""


@dataclass(frozen=True)
class SolverResult:
    best_value: Optional[int]
    best_distance: Optional[int]
    expressions: Tuple[str, ...]
    expression_count: int
    is_complete: bool
    elapsed_seconds: float


@dataclass(frozen=True)
class NormalizedExpression:
    text: str
    key: str
    precedence: int
    operator: Optional[str] = None


class ExpressionValidationError(ValueError):
    """Raised when a submitted arithmetic expression is not allowed."""


class IntegerExpressionEvaluator:
    """Evaluate simple integer arithmetic expressions safely."""

    def __init__(self, available_numbers: Sequence[int]) -> None:
        self._available_numbers = Counter(available_numbers)

    def evaluate(self, expression: str) -> ExpressionEvaluation:
        if not expression.strip():
            return ExpressionEvaluation(False, None, "No calculation was declared")

        try:
            parsed_expression = ast.parse(expression, mode="eval")
            value, used_numbers = self._evaluate_node(parsed_expression.body)
            self._validate_used_numbers(used_numbers)
        except (SyntaxError, ExpressionValidationError) as exc:
            return ExpressionEvaluation(False, None, str(exc))

        return ExpressionEvaluation(True, value)

    def _evaluate_node(self, node: ast.AST) -> Tuple[int, Counter[int]]:
        if isinstance(node, ast.Constant):
            return self._evaluate_constant(node)

        if isinstance(node, ast.BinOp):
            left_value, left_numbers = self._evaluate_node(node.left)
            right_value, right_numbers = self._evaluate_node(node.right)
            value = self._apply_binary_operation(left_value, right_value, node.op)
            return value, left_numbers + right_numbers

        raise ExpressionValidationError("Only numbers, parentheses, +, -, *, and / are allowed")

    @staticmethod
    def _evaluate_constant(node: ast.Constant) -> Tuple[int, Counter[int]]:
        if isinstance(node.value, bool) or not isinstance(node.value, int):
            raise ExpressionValidationError("Only integer numbers are allowed")
        return node.value, Counter([node.value])

    @staticmethod
    def _apply_binary_operation(left_value: int, right_value: int, operation: ast.operator) -> int:
        if isinstance(operation, ast.Add):
            return left_value + right_value
        if isinstance(operation, ast.Sub):
            return left_value - right_value
        if isinstance(operation, ast.Mult):
            return left_value * right_value
        if isinstance(operation, ast.Div):
            if right_value == 0:
                raise ExpressionValidationError("Division by zero is not allowed")
            if left_value % right_value != 0:
                raise ExpressionValidationError("Division must produce an integer result")
            return left_value // right_value
        raise ExpressionValidationError("Only +, -, *, and / are allowed")

    def _validate_used_numbers(self, used_numbers: Counter[int]) -> None:
        overused_numbers = used_numbers - self._available_numbers
        if not overused_numbers:
            return

        details = ", ".join(
            f"{number} used {count} too many time(s)"
            for number, count in sorted(overused_numbers.items())
        )
        raise ExpressionValidationError(
            f"Numbers may only be used as many times as drawn: {details}"
        )


def ask_big_number_count() -> int:
    while True:
        response = input("How many big numbers [0-4]? ").strip()
        try:
            big_number_count = int(response)
        except ValueError:
            print("Please enter an integer between 0 and 4.")
            continue

        if MIN_BIG_NUMBER_COUNT <= big_number_count <= MAX_BIG_NUMBER_COUNT:
            return big_number_count
        print("Please enter an integer between 0 and 4.")


def draw_number_round(big_number_count: int) -> NumberRound:
    if not MIN_BIG_NUMBER_COUNT <= big_number_count <= MAX_BIG_NUMBER_COUNT:
        raise ValueError("Number of big numbers must be between 0 and 4.")

    small_number_count = NUMBER_COUNT - big_number_count
    selected_numbers = list(random.sample(BIG_NUMBERS, big_number_count))
    selected_numbers.extend(random.sample(SMALL_NUMBER_POOL, small_number_count))
    random.shuffle(selected_numbers)
    target = random.randint(MIN_TARGET, MAX_TARGET)
    return NumberRound(numbers=tuple(selected_numbers), target=target)


def evaluate_expression(expression: str, available_numbers: Sequence[int]) -> ExpressionEvaluation:
    evaluator = IntegerExpressionEvaluator(available_numbers)
    return evaluator.evaluate(expression)


def score_distance(distance: Optional[int]) -> int:
    if distance is None:
        return 0
    if distance == 0:
        return 10
    if 1 <= distance <= 5:
        return 7
    if 6 <= distance <= 10:
        return 5
    return 0


def solve_number_round(
    numbers: Sequence[int],
    target: int,
    time_limit_seconds: int = DEFAULT_SOLVER_TIME_LIMIT_SECONDS,
) -> SolverResult:
    start_time = time.monotonic()
    deadline = start_time + time_limit_seconds
    subset_solutions: Dict[int, Dict[int, Set[str]]] = {}
    is_complete = True

    for index, number in enumerate(numbers):
        subset_solutions[1 << index] = {number: {str(number)}}

    for mask in range(1, 1 << len(numbers)):
        if mask in subset_solutions:
            continue
        if _is_past_deadline(deadline):
            is_complete = False
            break
        subset_solutions[mask] = _solve_subset(mask, subset_solutions, deadline)
        if _is_past_deadline(deadline):
            is_complete = False
            break

    return _build_solver_result(subset_solutions, target, is_complete, start_time)


def _solve_subset(
    mask: int,
    subset_solutions: Dict[int, Dict[int, Set[str]]],
    deadline: float,
) -> Dict[int, Set[str]]:
    solutions: DefaultDict[int, Set[str]] = defaultdict(set)
    left_mask = (mask - 1) & mask

    while left_mask:
        right_mask = mask ^ left_mask
        if left_mask < right_mask:
            _combine_subset_solutions(
                solutions,
                subset_solutions[left_mask],
                subset_solutions[right_mask],
                deadline,
            )
            if _is_past_deadline(deadline):
                break
        left_mask = (left_mask - 1) & mask

    return dict(solutions)


def _combine_subset_solutions(
    solutions: DefaultDict[int, Set[str]],
    left_solutions: Dict[int, Set[str]],
    right_solutions: Dict[int, Set[str]],
    deadline: float,
) -> None:
    for left_value, left_expressions in left_solutions.items():
        for right_value, right_expressions in right_solutions.items():
            for left_expression in left_expressions:
                for right_expression in right_expressions:
                    _add_combined_solutions(
                        solutions,
                        left_value,
                        right_value,
                        left_expression,
                        right_expression,
                    )
                    if _is_past_deadline(deadline):
                        return


def _add_combined_solutions(
    solutions: DefaultDict[int, Set[str]],
    left_value: int,
    right_value: int,
    left_expression: str,
    right_expression: str,
) -> None:
    _add_solution(
        solutions,
        left_value + right_value,
        f"({left_expression} + {right_expression})",
    )
    _add_solution(
        solutions,
        left_value * right_value,
        f"({left_expression} * {right_expression})",
    )
    _add_solution(
        solutions,
        left_value - right_value,
        f"({left_expression} - {right_expression})",
    )
    _add_solution(
        solutions,
        right_value - left_value,
        f"({right_expression} - {left_expression})",
    )

    if right_value != 0 and left_value % right_value == 0:
        _add_solution(
            solutions,
            left_value // right_value,
            f"({left_expression} / {right_expression})",
        )
    if left_value != 0 and right_value % left_value == 0:
        _add_solution(
            solutions,
            right_value // left_value,
            f"({right_expression} / {left_expression})",
        )


def _add_solution(
    solutions: DefaultDict[int, Set[str]],
    value: int,
    expression: str,
) -> None:
    solutions[value].add(expression)


def _build_solver_result(
    subset_solutions: Dict[int, Dict[int, Set[str]]],
    target: int,
    is_complete: bool,
    start_time: float,
) -> SolverResult:
    value_to_expressions: DefaultDict[int, Set[str]] = defaultdict(set)
    for solutions in subset_solutions.values():
        for value, expressions in solutions.items():
            value_to_expressions[value].update(expressions)

    if not value_to_expressions:
        return SolverResult(None, None, tuple(), 0, is_complete, time.monotonic() - start_time)

    best_value = min(value_to_expressions, key=lambda value: abs(target - value))
    expressions = _normalized_unique_expressions(value_to_expressions[best_value])
    return SolverResult(
        best_value=best_value,
        best_distance=abs(target - best_value),
        expressions=expressions,
        expression_count=len(expressions),
        is_complete=is_complete,
        elapsed_seconds=time.monotonic() - start_time,
    )


def _normalized_unique_expressions(expressions: Set[str]) -> Tuple[str, ...]:
    normalized_expressions = {
        _normalize_expression_text(expression)
        for expression in expressions
    }
    return tuple(sorted(normalized_expressions, key=_expression_cognitive_load))


def _expression_cognitive_load(expression: str) -> Tuple[int, int, int, int, str]:
    try:
        parsed_expression = ast.parse(expression, mode="eval")
    except SyntaxError:
        return sys.maxsize, sys.maxsize, sys.maxsize, len(expression), expression

    operator_count, operator_cost, number_count = _expression_cognitive_load_for_node(
        parsed_expression.body
    )
    return operator_count, operator_cost, number_count, len(expression), expression


def _expression_cognitive_load_for_node(node: ast.AST) -> Tuple[int, int, int]:
    if isinstance(node, ast.Constant):
        return 0, 0, 1

    if isinstance(node, ast.BinOp):
        left_operator_count, left_operator_cost, left_number_count = (
            _expression_cognitive_load_for_node(node.left)
        )
        right_operator_count, right_operator_cost, right_number_count = (
            _expression_cognitive_load_for_node(node.right)
        )
        return (
            left_operator_count + right_operator_count + 1,
            left_operator_cost + right_operator_cost + _operation_cognitive_cost(node.op),
            left_number_count + right_number_count,
        )

    return sys.maxsize, sys.maxsize, sys.maxsize


def _operation_cognitive_cost(operation: ast.operator) -> int:
    if isinstance(operation, ast.Add):
        return 1
    if isinstance(operation, ast.Mult):
        return 2
    if isinstance(operation, ast.Sub):
        return 3
    if isinstance(operation, ast.Div):
        return 4
    return sys.maxsize


def _normalize_expression_text(expression: str) -> str:
    normalized_expression = expression
    for _ in range(3):
        next_expression = _render_root_expression(_normalize_expression(normalized_expression))
        if next_expression == normalized_expression:
            return next_expression
        normalized_expression = next_expression
    return normalized_expression


def _normalize_expression(expression: str) -> NormalizedExpression:
    try:
        parsed_expression = ast.parse(expression, mode="eval")
    except SyntaxError:
        return NormalizedExpression(expression, expression, sys.maxsize)

    return _normalize_expression_node(parsed_expression.body)


def _normalize_expression_node(node: ast.AST) -> NormalizedExpression:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int):
            return NormalizedExpression(str(node.value), f"invalid:{node.value}", sys.maxsize)
        return NormalizedExpression(str(node.value), f"number:{node.value}", 4)

    if not isinstance(node, ast.BinOp):
        return NormalizedExpression(ast.dump(node), ast.dump(node), sys.maxsize)

    operator = _operation_symbol(node.op)
    left_expression = _normalize_expression_node(node.left)
    right_expression = _normalize_expression_node(node.right)

    if operator in {"+", "-"}:
        return _normalize_additive_expression(node)

    if operator == "*":
        return _normalize_associative_expression(
            operator,
            left_expression,
            right_expression,
        )

    return _normalize_ordered_expression(operator, left_expression, right_expression)


def _operation_symbol(operation: ast.operator) -> str:
    if isinstance(operation, ast.Add):
        return "+"
    if isinstance(operation, ast.Mult):
        return "*"
    if isinstance(operation, ast.Sub):
        return "-"
    if isinstance(operation, ast.Div):
        return "/"
    return "?"


def _normalize_additive_expression(node: ast.AST) -> NormalizedExpression:
    signed_terms = _collect_additive_terms(node, sign=1)
    positive_terms = sorted(
        (term for sign, term in signed_terms if sign > 0),
        key=_normalized_operand_sort_key,
    )
    negative_terms = sorted(
        (term for sign, term in signed_terms if sign < 0),
        key=_normalized_operand_sort_key,
    )

    terms = _format_additive_terms(positive_terms, negative_terms)
    key = "add:" + ",".join(
        [f"+{term.key}" for term in positive_terms]
        + [f"-{term.key}" for term in negative_terms]
    )
    return NormalizedExpression(
        text=terms,
        key=key,
        precedence=_operator_precedence("+"),
        operator="+",
    )


def _collect_additive_terms(
    node: ast.AST,
    sign: int,
) -> List[Tuple[int, NormalizedExpression]]:
    if isinstance(node, ast.BinOp):
        operator = _operation_symbol(node.op)
        if operator == "+":
            terms = _collect_additive_terms(node.left, sign)
            terms.extend(_collect_additive_terms(node.right, sign))
            return terms
        if operator == "-":
            terms = _collect_additive_terms(node.left, sign)
            terms.extend(_collect_additive_terms(node.right, -sign))
            return terms

    return [(sign, _normalize_expression_node(node))]


def _format_additive_terms(
    positive_terms: List[NormalizedExpression],
    negative_terms: List[NormalizedExpression],
) -> str:
    if positive_terms:
        text = " + ".join(
            _format_expression_child(term, "+", is_right_child=False)
            for term in positive_terms
        )
    else:
        text = "0"

    for term in negative_terms:
        text = f"{text} - {_format_expression_child(term, '+', is_right_child=False)}"

    return text


def _normalize_associative_expression(
    operator: str,
    left_expression: NormalizedExpression,
    right_expression: NormalizedExpression,
) -> NormalizedExpression:
    operands = _flatten_associative_operands(operator, left_expression)
    operands.extend(_flatten_associative_operands(operator, right_expression))
    operands.sort(key=_normalized_operand_sort_key)

    text = f" {operator} ".join(
        _format_expression_child(operand, operator, is_right_child=False)
        for operand in operands
    )
    key = f"{operator}:" + ",".join(operand.key for operand in operands)
    return NormalizedExpression(
        text=text,
        key=key,
        precedence=_operator_precedence(operator),
        operator=operator,
    )


def _flatten_associative_operands(
    operator: str,
    expression: NormalizedExpression,
) -> List[NormalizedExpression]:
    if expression.operator != operator:
        return [expression]

    parsed_expression = ast.parse(_render_root_expression(expression), mode="eval")
    return _collect_associative_operands(operator, parsed_expression.body)


def _collect_associative_operands(
    operator: str,
    node: ast.AST,
) -> List[NormalizedExpression]:
    if not isinstance(node, ast.BinOp) or _operation_symbol(node.op) != operator:
        return [_normalize_expression_node(node)]

    operands = _collect_associative_operands(operator, node.left)
    operands.extend(_collect_associative_operands(operator, node.right))
    return operands


def _normalize_ordered_expression(
    operator: str,
    left_expression: NormalizedExpression,
    right_expression: NormalizedExpression,
) -> NormalizedExpression:
    left_text = _format_expression_child(left_expression, operator, is_right_child=False)
    right_text = _format_expression_child(right_expression, operator, is_right_child=True)
    return NormalizedExpression(
        text=f"{left_text} {operator} {right_text}",
        key=f"{operator}:{left_expression.key},{right_expression.key}",
        precedence=_operator_precedence(operator),
        operator=operator,
    )


def _format_expression_child(
    expression: NormalizedExpression,
    parent_operator: str,
    is_right_child: bool,
) -> str:
    parent_precedence = _operator_precedence(parent_operator)
    needs_parentheses = expression.precedence < parent_precedence
    if is_right_child and parent_operator in {"-", "/"}:
        needs_parentheses = needs_parentheses or expression.precedence <= parent_precedence

    if needs_parentheses:
        return _render_root_expression(expression)
    return expression.text


def _render_root_expression(expression: NormalizedExpression) -> str:
    if expression.operator is None:
        return expression.text
    return f"({expression.text})"


def _normalized_operand_sort_key(expression: NormalizedExpression) -> Tuple[int, int, str]:
    return _expression_cognitive_load(expression.text), len(expression.text), expression.key


def _operator_precedence(operator: str) -> int:
    if operator in {"+", "-"}:
        return 1
    if operator in {"*", "/"}:
        return 2
    return sys.maxsize


def _is_past_deadline(deadline: float) -> bool:
    return time.monotonic() > deadline


def play_number_round(timer_seconds: int) -> None:
    big_number_count = ask_big_number_count()
    number_round = draw_number_round(big_number_count)

    with ThreadPoolExecutor(max_workers=1) as executor:
        solver_future = executor.submit(
            solve_number_round,
            number_round.numbers,
            number_round.target,
            DEFAULT_SOLVER_TIME_LIMIT_SECONDS,
        )

        print(f"Selected numbers: {_format_selected_numbers(number_round.numbers)}")
        print(f"Target: {number_round.target}")
        _wait_for_ready_or_timeout(timer_seconds)
        evaluation = _read_user_evaluation(number_round)
        _print_user_result(evaluation, number_round)
        solver_result = solver_future.result()
        _print_solver_result(solver_result, number_round.target)


def _format_selected_numbers(numbers: Sequence[int]) -> str:
    big_numbers = [number for number in numbers if number in BIG_NUMBERS]
    small_numbers = [number for number in numbers if number in SMALL_NUMBERS]
    display_numbers = big_numbers + small_numbers
    return " ".join(str(number) for number in display_numbers)


def _read_user_evaluation(number_round: NumberRound) -> ExpressionEvaluation:
    while True:
        expression = input("Enter your calculation [empty-enter for no answer]: ").strip()
        evaluation = evaluate_expression(expression, number_round.numbers)
        if evaluation.is_valid or not expression:
            return evaluation

        print(f"Invalid calculation: {evaluation.error}.")
        print("Try again, or press Enter for no answer.")


def _wait_for_ready_or_timeout(seconds: int) -> None:
    if seconds <= 0:
        return

    print("Press Enter when ready, or wait for the timer.")
    for remaining_seconds in range(seconds, 0, -1):
        print(f"\r{remaining_seconds:3d} seconds left", end="", flush=True)
        try:
            ready_inputs, _, _ = select.select([sys.stdin], [], [], 1)
        except (OSError, ValueError):
            time.sleep(1)
            ready_inputs = []
        if ready_inputs:
            sys.stdin.readline()
            print("\rReady.            ")
            return
    print("\rTimes up!         ")


def _print_user_result(
    evaluation: ExpressionEvaluation,
    number_round: NumberRound,
) -> None:
    if not evaluation.is_valid or evaluation.value is None:
        print(f"{evaluation.error}. 0 points!")
        print()
        return

    distance = abs(number_round.target - evaluation.value)
    points = score_distance(distance)
    print(
        f"Your result is {evaluation.value}. "
        f"Target is {number_round.target}. "
        f"Distance is {distance}. "
        f"{points} points!"
    )
    print()


def _print_solver_result(solver_result: SolverResult, target: int) -> None:
    if solver_result.best_value is None or solver_result.best_distance is None:
        print("No solver result is available.")
        print()
        return

    status = "complete" if solver_result.is_complete else "stopped at the time limit"
    print(
        f"Solver result ({status}, {solver_result.elapsed_seconds:.2f} seconds): "
        f"best value {solver_result.best_value}, "
        f"distance {solver_result.best_distance} from target {target}."
    )
    print(f"Found {solver_result.expression_count} expression(s) for this best value.")

    for expression in solver_result.expressions[:MAX_SOLUTIONS_TO_PRINT]:
        print(f"\t{expression}")

    remaining_count = solver_result.expression_count - MAX_SOLUTIONS_TO_PRINT
    if remaining_count > 0:
        print(f"\t... and {remaining_count} more")
    print()
