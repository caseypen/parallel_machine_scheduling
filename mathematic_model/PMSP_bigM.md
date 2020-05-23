### Formulation of Predictive Scheduling of FRAIL-Bots under stochastic request prediction (Time-Index-Model)

#### 1. Description

Predictive scheduling of FRAIL-Bots under deterministic requests prediction has been modeled into parallel machine scheduling problem with job release time. The job release time and job process time are calculated based on predictive requests, including full tray location and full tray time. In practice, the predicted requests are not deterministic but with some uncertainty. Consequently, the job release time and process time is stochastic following the know probability distribution. Hence, a stochastic program is formulated to achieve the optimal solution considering the uncertain information.

#### 2. Formulation

The predictive scheduling of the crop-transporting robots can be formulated as stochastic program. The predictive transporting requests are generated when the fill ratio of the tray is up to certain value. The request includes full tray time of harvesting tray $\Delta t^f_i$and full tray location $L^f_i$, where $\Delta t^f_i \sim \xi^f_i$, $\xi_i^f$ is the estimated probability distribution of full tray time prediction and $L^f_i \sim \xi^{L_f}_i$, $\xi_i^f$ is the estimated probability distribution of full tray location. Given $\Delta \xi^f_i$ and $\xi^{L^f}_i$, we can sample the deterministic $\Delta t^f_i(\omega)$ and $L^f_i(\omega)$ in each scenario $\omega$, from which we can generate the request time $\Delta t^ r_i(\omega)$ and $\Delta t^p_i(\omega)$ in that scenario. The sampled scenarios are formulated as a finite set $\Omega$. The whole problem can be formulated as below:

$1.\ Parameters$

$i,j$: index of jobs (transporting requests);

$k$: index of machines (FRAIL-Bots);

$\Delta t^r_i (\omega)$: job release time of the request i in the scenario $\omega$;

$\Delta t^p_i (\omega)$: job process time of the request i in the scenario $\omega$;

$\Delta t^a_i (\omega)$: machine available time of the request i in the scenario $\omega$;

$I$: set of jobs ;

$J$: $J=I\cup\{0\}$, where $\{0\}$ is a dummy job serving as the predecessor of the first job and the successor of the last job processed on a machine. The release time and process time of the dummy job is equal to 0; 

$M$: set of machines (FRAIL-Bots);

$\Omega$: set of scenarios, which consists of a finite number of scenarios;

$bigM$: a very large number;

$2.\ Decision\ variables$

$t^C_i(\omega)$: complete time of job $i\in J$

$x_{ij}^k$: a binary value if job $i$ is scheduled on the machine $k$ and processed at time $t$;

$3.\ Stochastic\ Program\ Formulations$

$min\ g_{stoch} = \mathbb{E}_{\Omega}\sum\limits_{i\in J}\Delta t^C_i(\omega)$

$s.t.\ $

$\sum\limits_{k\in M}\sum\limits_{t\in TB} \chi_{ik}^t(\omega) \leq 1, i\in J, \omega\in \Omega\ \ \ (2)$

$\sum\limits_{k\in M}\sum\limits_{i\in J,i\neq j}x_{ij}^k=1, i\in J\ \ \ (3)$

$\sum\limits_{l\in J,l\neq i}x^k_{il}-\sum\limits_{l\in J,l\neq i}x^k_{li}=0 \ \ \ (4)$

$C_i(\omega)\geq \sum\limits_{k\in M}(\Delta t^a_k(\omega)\times\sum\limits_{j\in J,j\ne i}x_{ij}^k) + \Delta t_i^r + \Delta t^p_i, i\in I, j\in J, j\ne i,$

The objective function $g_{stoch}$ is to minimize the expectation of the total completion time. Constraint (1) restricts that one job can only be processed by one machine. Constraint (2) states that one job can only be done once. Constraint (3) ensures that the job can only be processed after the release constraint. Constraint (4) implies that the job cannot be processed until the machine is available. Constraint (5) expresses the completion time of each job $i$. 

#### 3. SAA method

SAA (Sampling  Average Approximation) is an approach for solving stochastic optimization problem by deterministic techniques using Monte Carlo simulation. It is a popular and easy to implement approach to address this stochastic problems, and it performs well under sufficient number of scenarios. After sampling multiple scenarios $\Omega$, the expectation of the total completion time can be approximated by the average, $\hat{g}_{SAA}$ of all sampled scenarios, where $\hat{g}_{SAA}=\frac{1}{N}\sum\limits_{\omega=1}^N\sum\limits_{i\in J}\Delta t^C_i(\omega)$. Given this, the formulated problem can be solved by the commercial solver Gurobi for the small number of scenarios.

The average optimal value $\hat{g}_{SAA}$ can also be written as $\hat{g}_{SAA}=\sum\limits_{i\in J}\frac{1}{N}\sum\limits_{\omega=1}^N\Delta t^C_i(\omega)$. We use $\hat{g}_j$ to express the value of $\frac{1}{N}\sum\limits_{\omega=1}^N\Delta t^C_i(\omega)$, so $\hat{g}_{SAA}=\sum\limits_{i\in J}\hat{g}_{j}$. When we calculate $\hat{g}_{SAA}$, the value of $\hat{\mathbf{g}}=\{\hat{g}_1, \hat{g}_2, \ldots, \hat{g}_J\}$ is also figured out and given the $\mathbf{g}$, we can obtain the scheduling policy $\hat{x}=f(\hat{\mathbf{g}})$. For the optimal expression of the objective function $g_{stoch} = \sum\limits_{i\in J}\mathbb{E}_{\Omega}\Delta t^C_i(\omega)=\sum\limits_{i\in J}g_j$, when $\hat{g}_{SAA}$ converges to $g_{stoch}$, $\hat{\mathbf{g}}$ converges to $\mathbf{g}$. Therefore the scheduling result $\hat{x}$ will converge to $x_{opt}$.