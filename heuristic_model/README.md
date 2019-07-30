## Parallel Machine Scheduling with Release Constraint
### Introduction

Parallel machine scheduling problems with release constraints, $Pm|r_j|\sum C_j$, has been proved NP-hard in strong sense. This repository is to use Branch and Bound algorithm to solve it, as well as an approximate algorithm, SRPT-CONVERT. The code is implemented in C and Python-API is wrapped with Cython package.

### Problem definition

$M$ machines needs to process $N$ jobs. Each job is associated with a release constraint and a process time interval. Each machine is not available to start processing jobs until the available time is up to (processing some jobs not in $N$ jobs). The objective is to have the machines finish processing all jobs. The result is to have the Gantt chart to express the schedule of the whole machines. 

- Input: 
  - request_ids: ids of jobs to be processed;
  - release_times: time interval of jobs released to be processed;
  - process_intervals: time interval to process a job, non preemptive is assumed;
  - machine_available_times: time interval of machines available to start processing jobs;
- Output:
  - Gantt Chart of jobs and machines;

### Approximate algorithm

- SRPT-CONVERT:
  - Delete the non-preemptive constraint to change the problem to a P-solvable problem, $Pm|r_j, pmtm|\sum C_i$, by releasing the non-preemptive constraints.
  - CONVERT algorithm is used to transform the preemptive schedules to non-preemptive one.

### Exact algorithm

- Branch and bound search
  - Bounds I:
    -  $Pm||\sum C_i$, delete release constraints;
    - Solution: Shortest-Process-Time (SPT)
  - Bounds II:
    - $Pm|r_j, pmtm|\sum C_i$, delete non-preemptive constraints;
    - Solution: Shortest-Remaining-Process-Time (SRPT);

### Running the code

- Compile the code: make all;
- Try the demo: python demo.py;