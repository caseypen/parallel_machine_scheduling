## Parallel machine scheduling problem (PMSP)-II

### Summary
There are M parallel machines and N to-do jobs. Each job is integrated with a release time and process time. The goal is to minimize the total completion time of all jobs. The (integer) discrete time model is used.

### Sets
- $\mathcal{S}_M$ = set of machines, initialize with machine ids; 
- $\mathcal{S}_J$ = set of jobs, initialize with job ids;
- $\mathcal{S}_{time}$ = set of discrete time in integer: $TB\times 1$;
  - $TB$ can be estimated from approximate algorithm;

### Parameters
- $t^r_i$ : Release time of jobs $N\times1$;
- $t^p_i$ : Process time of jobs $N\times1$; 
- $t^A_k$ : Available time of machines $M\times1$;

### Variables
- $N$ number of jobs;
- $M$ number of machines;
- $t^c_{i}$ complete time of job $i\in \mathcal{S}_J$;
- $\chi_{ikt}$: a binary value if job $i$ is scheduled on machine $k$ and processed at time $t$, $N\times M\times TB$;


### Objectives
- minimize total completion time:
    $\sum_i^N t^c_{i}$


### Constraints
- One job can only be processed by one machine: $\sum_{i=0}^N\sum_{max(0, t-t_i^p)}^t\leq1, \forall k\in M$(C1)
- One job do once: $\sum^M_{k=0}\sum^{TB}_{t=0} \chi_{ikt} = 1, \forall i \in J$ (C2)
- Release constraint: $\sum_k^M\sum_t^{t^r_i-1}\chi_{ikt}=0 \ \forall i \in J$ (C3)
- Machine available time constraint: $\sum_i^N\sum_t^{t^r_i-1}\chi_{ikt}=0, \forall k\in M$ (C4)
- Completion time requirements: $\sum_k^M\sum_t^{TB}(t+t_i^p+t_k^A)\chi_{ikt}, \forall i\in J$ (C5).