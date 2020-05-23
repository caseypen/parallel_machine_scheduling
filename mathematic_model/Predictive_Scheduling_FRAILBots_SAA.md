### Two-stage stochastic program of Predictive Scheduling of FRAIL-Bots under stochastic request prediction (Time-Index-Model)

#### 1. Description

Predictive scheduling of FRAIL-Bots under deterministic requests prediction has been modeled into parallel machine scheduling problem with job release time. The job release time and job process time are calculated based on predictive transport requests, including full tray location and full tray time. However, in practice, the predicted requests are not deterministic but with some uncertainty. Consequently, the job release time and process time is stochastic distributed expressed as multiple possible scenarios. A stochastic program is formulated to achieve the optimal solution considering all the estimated scenarios.

#### 2. Formulation

The predictive scheduling of the crop-transporting robots can be formulated as stochastic program. The predictive transporting requests are generated when the fill ratio of the tray is up to certain value. The request includes full tray time of harvesting tray $\Delta t^f_i$and full tray location $L^f_i$, where $\Delta t^f_i \sim \Xi^f$ and $\xi_i^f$ is the predictive full tray time in the scenario $\omega_i$ and $L^f_i \sim \Xi^{L_f}$ and $\xi_i^{L_f}$ is the predictive full tray location in  scenario $\omega_i$. In each scenario $\omega$, we can generate the request time $\Delta t^ r_i(\omega)$ and $\Delta t^p_i(\omega)$ given $\xi_i^f$ and $\xi_i^{L_f}$. The sampled scenarios are formulated as a finite set $\Omega$. The whole problem can be formulated as below:

##### 1. Parameters

$i,j$: index of jobs (transporting requests);

$k$: index of machines (FRAIL-Bots);

$t$: index of the duration;

$\Delta t^r_i (\omega)$: job release time of the request i in the scenario $\omega$;

$\Delta t^p_i (\omega)$: job process time of the request i in the scenario $\omega$;

$\Delta t^a_i (\omega)$: machine available time of the request i in the scenario $\omega$;

$J$: set of jobs (requests);

$M$: set of machines (FRAIL-Bots);

$TB$: upper bound for the makespan of machines, this can be estimated by heuristic policy;

$\Omega$: set of scenarios, which consists of a finite number of scenarios;

##### 2. Decision\ variables

$t^C_i(\omega)$: complete time of job $i\in J$

$\chi_{ik}^t(\omega)$: a binary value if job $i$ is scheduled on the machine $k$ and starts processing at time $t$;

$z_{ik}$: a binary value if job $i$ is scheduled on the machine $k$. Notice that this one does not relate to the scenario.

##### 3. Two-Stage Stochastic Program Formulations

This problem can be modeled as two-stage stochastic programming. The first stage is to solve the assignment variable $z_{ik}$. When $z_{ik}$ is decided, the problem is changed to a one machine scheduling problem, which can be solved with a heuristic rule Earliest Release Time.

$min\ g_{stoch} = \mathbb{E}_{\Omega}\sum\limits_{i\in J}\Delta t^C_i(\omega)$

$s.t.\ $

$\sum\limits_{k\in M}\sum\limits_{t\in TB} \chi_{ik}^t(\omega) = 1, i\in J, \omega\in \Omega\ \ \ (1)$

$\sum\limits_{j\in J}\sum\limits_{h=max(0,t-t^p_i)}^{t-1} \chi_{ik}^h(\omega) \leq 1,\ k\in M, \omega\in \Omega\ \ \ (2)$  

$\sum\limits_{k\in M}\sum\limits_{t=0}^{\Delta t^r_i-1} \chi_{ik}^t(\omega)=0, i\in J, \omega\in \Omega \ \ \ (3)$

$\sum\limits_{i\in J}\sum\limits_{t}^{\Delta t^a_i-1} \chi_{ik}^t(\omega) = 0, k\in M, \omega\in \Omega \ \ \ (4)$

$\sum\limits_{k\in M}\sum\limits_{t\in TB} \chi_{ik}^t(\omega)(t+\Delta t_i^p(\omega)+\Delta t_i^A(\omega)) = t_i^C(\omega), i\in J, \omega\in \Omega \ \ \ (5)$

$\sum\limits_{i\in J}\sum\limits_{k\in M}\chi_{ik}^t(\omega) \leq z_{ik},\ \ t\in TB\ \ \ (6)$

The objective function $g_{stoch}$ is to minimize the expectation of the total completion time. Constraint (1) restricts that one job can only be processed by one machine. Constraint (2) states that one job can only be done once. Constraint (3) ensures that the job can only be processed after the release constraint. Constraint (4) implies that the job cannot be processed until the machine is available. Constraint (5) expresses the completion time of each job $i$. Constraint (6) is to guarantee that the the job processed by machine $k$ must be assigned on that machine.

#### 3. SAA method

SAA (Sampling  Average Approximation) is an approach for solving stochastic optimization problem by deterministic techniques using Monte Carlo simulation. It is a popular and easy to implement approach to address this stochastic problems, and it performs well under sufficient number of scenarios. After sampling multiple scenarios $\Omega$, the expectation of the total completion time can be approximated by the average, $\hat{g}_{SAA}$ of all sampled scenarios, where $\hat{g}_{SAA}=\frac{1}{N}\sum\limits_{\omega=1}^N\sum\limits_{i\in J}\Delta t^C_i(\omega)$. Given this, the formulated problem can be solved by the commercial solver Gurobi for the finite number of scenarios. Then the assignment of $z_{ik}$ can be solved from the stochastic program. Given the results of $z_{ik}$, then under each scenario,  jobs are scheduled according to the modified SPT method: the job is firstly sorted in the ascending order based on the processing times, the shortest job among those not yet processed but released will be put on the machine. The order on different scenarios are combined to formulate a consensus order for multiple scenarios. 















