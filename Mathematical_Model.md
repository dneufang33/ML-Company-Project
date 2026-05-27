## Oerlikon Short‑Horizon MILP – Mathematical Formulation

### Sets

| Symbol              | Description                                                        |
| ------------------- | ------------------------------------------------------------------ |
| $I$                 | Coating (product) IDs                                              |
| $T = \{0,\dots,4\}$ | Planning days ($0=$ today, $4=$ today + 4)                         |
| $A = \{0,1,2,3,4\}$ | Backlog‑age buckets ($0=$ arrives today, $4=$ last day before due) |

---

### Parameters

| Symbol                  | Meaning                                                  | Typical value |
| ----------------------- | -------------------------------------------------------- | ------------- |
| $M$                     | Number of coating machines                               | 65 (param.)   |
| $B_{\text{reg}}$        | Regular batches **per machine per day**                  | 2             |
| $B_{\text{ot}}$         | Overtime batches **per machine per day**                 | 1             |
| $Q$                     | Volume capacity per batch                                | 1             |
| $c_{\text{reg}}$        | Cost per regular batch                                   | €150          |
| $c_{\text{ot}}$         | Cost per overtime batch                                  | €300          |
| $\gamma$                | Early‑delivery bonus per **unit** and per day gained     | €50           |
| $\lambda$               | Penalty per unit left unprocessed after day 4 (ages 0–3) | 100           |
| $d_{i,t}$               | Forecasted arrivals for coating $i$ on day $t$           | data          |
| $s^{\text{init}}_{i,a}$ | Backlog of age $a$ at the start of day 0                 | data          |

Site‑level capacities

$$
C_{\text{reg}} = M\,B_{\text{reg}}, 
\qquad
C_{\text{ot}}   = M\,B_{\text{ot}} .
$$

---

### Decision variables

| Variable               | Domain               | Interpretation                                        |
| ---------------------- | -------------------- | ----------------------------------------------------- |
| $p_{i,t,a}$            | $\mathbb{R}_{\ge 0}$ | Volume of age‑$a$ backlog coated on day $t$           |
| $s_{i,t,a}$            | $\mathbb{R}_{\ge 0}$ | Backlog of age $a$ **before** production on day $t$   |
| $n^{\text{reg}}_{i,t}$ | $\mathbb{Z}_{\ge 0}$ | Regular batches scheduled for coating $i$ on day $t$  |
| $n^{\text{ot}}_{i,t}$  | $\mathbb{Z}_{\ge 0}$ | Overtime batches scheduled for coating $i$ on day $t$ |

---

### Objective — maximise net profit

$$
\max
\Biggl[
   \underbrace{\sum_{i\in I}\sum_{t\in T}\sum_{a\in A}
       \gamma\,(4-a)\,p_{i,t,a}}_{\text{early‑delivery bonuses}}
   \;-\;
   \underbrace{c_{\text{reg}}\sum_{i\in I}\sum_{t\in T} n^{\text{reg}}_{i,t}}_{\text{regular‑batch cost}}
   \;-\;
   \underbrace{c_{\text{ot}}\sum_{i\in I}\sum_{t\in T} n^{\text{ot}}_{i,t}}_{\text{overtime cost}}
   \;-\;
   \underbrace{\lambda
      \sum_{i\in I}\sum_{a=0}^{3}
      \bigl(s_{i,4,a}-p_{i,4,a}\bigr)}_{\text{penalty for residual backlog}}
\Biggr]
$$

(The penalty applies only to ages 0–3 **after** day‑4 production; age‑4 units are forced
out by Constraint 3.)

---

### Constraints

1. **Backlog ageing**

   $$
   \begin{aligned}
   s_{i,0,a} &= s^{\text{init}}_{i,a}
       &&\forall\, i,\,a\\[2pt]
   s_{i,t,0} &= d_{i,t}
       &&\forall\, i,\,t\\[2pt]
   s_{i,t,a} &= s_{i,t-1,a-1} - p_{i,t-1,a-1}
       &&\forall\, i,\,t\ge 1,\,a\ge 1
   \end{aligned}
   $$

2. **Process only what exists**

   $$
   0 \le p_{i,t,a} \le s_{i,t,a}
   \qquad \forall\, i,t,a
   $$

3. **Due‑date clearance for bucket 4**

   $$
   p_{i,t,4} = s_{i,t,4}
   \qquad \forall\, i,t
   $$

4. **Batch–volume link**

   $$
   \sum_{a\in A} p_{i,t,a}
      \le
      \bigl(n^{\text{reg}}_{i,t} + n^{\text{ot}}_{i,t}\bigr)\,Q
   \qquad \forall\, i,t
   $$

5. **Site capacities**

   $$
   \sum_{i\in I} n^{\text{reg}}_{i,t} \le C_{\text{reg}},
   \qquad
   \sum_{i\in I} n^{\text{ot}}_{i,t}  \le C_{\text{ot}}
   \qquad \forall\, t
   $$

6. **Per‑coating batch bounds**

   $$
   0 \le n^{\text{reg}}_{i,t} \le B_{\text{reg}},
   \qquad
   0 \le n^{\text{ot}}_{i,t}  \le B_{\text{ot}}
   \qquad \forall\, i,t
   $$

7. **Variable domains**

   $$
   p_{i,t,a},\; s_{i,t,a} \in \mathbb{R}_{\ge 0},\qquad
   n^{\text{reg}}_{i,t},\; n^{\text{ot}}_{i,t} \in \mathbb{Z}_{\ge 0}
   $$

---

### FIFO property

Because age‑4 units **must** be processed on the day they appear (Constraint 3),
older backlog always leaves the system before younger backlog.
Any units of age 0–3 remaining after day 4 incur the penalty $\lambda$,
ensuring the model prefers early production whenever economically feasible.
