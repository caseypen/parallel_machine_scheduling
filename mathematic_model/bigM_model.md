## Parallel machine scheduling problem (PMSP)
### Summary
There are M parallel machines and N to-do jobs. Each job is integrated with a release time and process time. The goal is to minimize the total completion time of all jobs; The PMSP can be formulated as below. BigM theory is used to model this problem.

### Sets
- $\mathcal{S}_M$ = set of machines, initialize with machine ids; 
- $\mathcal{S}_J$ = set of jobs, initialize with job ids;
- $\mathcal{S}_{PAIRS}$ = set of machine-job schedules: $N\times N$ $(i < j)$. 

### Parameters
- $t_r$ = release time of jobs $N\times1$;
- $t_p$ = process time of jobs $N\times1$; 
- $t_A$ = available time of machines $M\times1$

### Variables
- $N$ number of jobs;
- $M$ number of machines;
- $t^d_{i}$ start processing time of job $i\in \mathcal{S}_J$;
- $z_{ik}$: a binary value if job $i$ is scheduled on machine $k$, $N\times M$;
- $y_{ij}$: a binary value if $J_i$ is executed before $J_j$, $\mathcal{S}_{PAIRS}$; 


### Objectives
- minimize total completion time (same as total start time):
    $\sum_i^N t^d_{i}$


### Constraints
- release constraint: $t^d_{i}>=t^r_i \ \forall i \in J$ (C1)
- One job do once: $\sum^M_k x_{ki} = 1$ (C2)
- Disjunctive constraint:
    - $t^d_{j}\geq t^d_{i} + t^P_i - BigM((1-y_{ij})+(1-z_{jk})+(1-z_{ik})), k\in M, (i,j) \in \mathcal{S}_{PAIRS}$ (C3)
    - $t^d_{i}\geq t^d_{j} + t^P_j - BigM( (y_{ij})+(1-z_{jk})+(1-z_{ik})), k\in M, (i,j) \in \mathcal{S}_{PAIRS}$ (C4)
- Consecutive constraint: $y_{ij}+1\geq y_{il}+y_{lj}, (i,j), (i,l)\ and\ (j,l) \in \mathcal{S}_{PAIRS}$ (C5)
- Machine available constraint:
    
    - $t^d_j\geq t^A_k - BigM(1-z_{ik})$
    
    