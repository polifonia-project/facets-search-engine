Nested Words: representation of data with both a linear ordering and a hierarchically nested matching of items. 

**refs**

> Alur and Madhusudan
> Adding Nesting Structure to Words
> JACM 56(3), 2009.
> https://dl.acm.org/doi/abs/10.1145/1516512.1516518 

and

> Marcelo Arenas, Pablo Barceló & Leonid Libkin 
> Regular Languages of Nested Words: Fixed Points, Automata, and Synchronization
> Theory of Computing Systems volume 49, pages639–670, 2011.
> https://homepages.inf.ed.ac.uk/libkin/papers/tocs11.pdf

see also

- [Nested Words and Visibly Pushdown Languages](https://www.cis.upenn.edu/~alur/nw.html "https://www.cis.upenn.edu/~alur/nw.html")
  summary and biblio on newsted words and VPL by R. Alur
- [Motley-word automata](:/MotleyWords.md)
  A note on nested words by A. Blass, Y. Gurevich

---

**def. nested word**

- sequence in $[1..n]$ and
- matching relation $⇢$ in $\{ -\infty, 1,...,n \} \times \{ 1,...,n, +\infty \}$

such that:

- match always forward: 
  if  $i ⇢ j$  then $i < j$
- match do not share position: 
  $|\{ i \mid i ⇢ j \}| \leq 1$ and $|\{ j \mid i ⇢ j\} | \leq 1$ 
- match do not cross: 
  no $i ⇢ j$ and $i' ⇢ j'$ and $i < i' \leq j < j'$

ALT
Gurevitch, Blass definition (see [Motley-word automata](:/MotleyWords.md)) drops second condition:

- if $i ⇢ j$ and $i' ⇢ j'$  and $i \leq  i'$
  then either $i < j < i' < j'$  or $i < i' < j' < j$

![7adca4e6b7c97bdec137c0e9279a46da.png](/Users/jacquema/Documents/Articles/NW-SM/fig/7adca4e6b7c97bdec137c0e9279a46da.png)

---

**applications**:

- Executions of sequential structured programs: 
  matchs =  *calls* and *returns*

![edcf4673f7e83f9dd3305ac96aa7132a.png](/Users/jacquema/Documents/Articles/NW-SM/fig/edcf4673f7e83f9dd3305ac96aa7132a.png)

*program execution. en = new scope = call, ex = exit scope = return, rd = read, wr = write, sk = other.* 

- XML docs:
  matchs = *open-* and *close- tags*

- Annotated linguistic data: 
  tree bank = repository (corpora) with 
  sentences (linear order) + anotation (hierarchical structure)

![305408e681d7bc00c866f614b858a574.png](/Users/jacquema/Documents/Articles/NW-SM/fig/305408e681d7bc00c866f614b858a574.png)
*parsed sentence as nested word: I saw the old man with a dog today.* 

---

**usefulness**:

- queries that refer to both hierarchical and linear structure
  (not solely on word or tree)
- automata model (*Nested Word Automata*) for reading linear & hierarchical structure in the same time.

---

**Nested-Word Automata**

simple definition Blass and Alur
$(Q, Q_{in}, Q_f, \delta)$ over $\Sigma$ where $\delta = (\delta_c, \delta_i, \delta_r)$, 

- $\delta_c \subseteq Q \times \Sigma \times Q$, 
- $\delta_i \subseteq Q \times \Sigma \times Q$, 
- $\delta_r \subseteq Q \times Q \times \Sigma \times Q$. 

run over nested word $(a_1\ldots a_k, ⇢)$ = sequence $q_0, \ldots, q_k$ such that

- $q_0 \in Q_{in}$
- for all $i$ call position of $⇢$, $(q_{i-1}, a_i, q_i) \in \delta_c$, 
- for all $i$ internal position of $⇢$, $(q_{i-1}, a_i, q_i) \in \delta_i$, 
- for all $i$ return position of $⇢$,  with $j⇢i$,
  $(q_{i-1}, q_{j-1}, a_i, q_i) \in \delta_r$.

it means that at call position, the current state is pushed to the stack, and it is popped at return positions.
