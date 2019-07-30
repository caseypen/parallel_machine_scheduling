## Parallel machine scheduling problems

This repository is to solve the parallel machine scheduling problems with job release constraints in the objective of sum of completion times. Two methods are proposed. One method is to use heuristic idea to model the problem and solve the modeled problem with branch and bound algorithm. The algorithm is implemented in C to get fast enough speed for online case. Another method is to use Pyomo to model the problem into a mixed integer programming and solve it with the solver (CPLEX, GUROBI or GLPK).

- Heuristic model:
  - Release the constraints to convert the problem to a P problem and solve the converted problem to get bounds;
  - Search the optimal solution with Branch and Bound algorithm;
  - A fast and sub-optimal approximate solution is also implemented.
- Mixed integer programming:
  - Use Pyomo to mathematically model the problem;
  - Solve the problem with solver;
  - Interpret the solution to machine-jobs schedule;

The result is visualized and expressed with Gantt chart.
