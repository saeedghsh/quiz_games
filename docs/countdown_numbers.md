# Countdown numbers solver

The numbers game draws six numbers. The player chooses how many big numbers to
draw, from 0 to 4. Big numbers come from `25, 50, 75, 100` without repetition.
The remaining numbers come from `1` through `9`, with each small number
appearing at most twice in a single round. The target is a random integer from
100 to 999.

The submitted calculation is parsed with Python's `ast` module, not with `eval`.
The validator only accepts integer literals, parentheses, and the operators `+`,
`-`, `*`, and `/`. Division is only valid when it produces another integer. The
validator also counts the integer literals in the expression and rejects
calculations that use a drawn number too many times. Invalid non-empty
submissions do not end the round immediately; the player is asked to enter a
corrected expression or press Enter for no answer.

The solver uses dynamic programming over subsets of the six drawn numbers:

* For each single-number subset, the only reachable value is that number itself.
* For each larger subset, split it into two disjoint smaller subsets.
* Combine every value from the left subset with every value from the right
  subset using `+`, `-`, `*`, and exact integer `/`.
* Store each reachable integer value together with expressions that produce it.
* After all subsets are processed, pick the reachable value closest to the
  target. The player does not have to use all six numbers.

The solver is started in a background thread while the player timer is running.
The search has a 30-second deadline, although ordinary six-number rounds should
usually finish much faster. When showing examples, the app prints at most two
expressions and ranks them with a simple cognitive-load heuristic: fewer
operations first, then easier operators, then shorter expressions. Expressions
are normalized before display: associative `+` and `*` chains are flattened,
commutative operands are sorted, and equivalent variations such as `(3 + 2 + 3)`
and `(2 + 3 + 3)` are counted once.
