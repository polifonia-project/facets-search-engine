# Music Content Descriptors
18 janvier 2022  
Florent  
https://github.com/polifonia-project/facets-search-engine

Draft sur les descripteurs de contenu musical utilisés dans des documents précédents (articles orientés langages et code/doc de qparse) et évolutions plus récentes.

L'objectif de ces descripteurs était à l'origine différent de la recherche/indexation: génération ou transformation de partition... Mais le modèle est relativement ouvert et peut–être adapté à ce cas.

## principe
représentation structurée de contenu musical écrit, avec dans un même modèle

- des événements musicaux
- des relations entre ces événements,
  en particulier des relations temporelles.


## labeled ranked trees 
The representation of a music score is a ranked tree labeled with symbols in a finite ranked alphabet.

#### musical events
they are represented by nullary symbols (atoms) 

- note 
- rest
- continuation of event (tie, dot)
- blank (duration without event)
- ... ?

These events have no duration attributes, unlike MusicXML or MEI counterparts.
The duration and start time of each event are deducible from the embedding temporal operators (see description below).

The grace notes and chords can be constructed using the temporal operators below.

#### temporal operators
We consider musical time values in $\mathbb{Q}$, with a unit (MTU) = 1 measure (bar).

The following $n$-ary operators of $\Sigma$ ($n$ > 0) can be interpreted on temporal durations (MTU domain $D = \mathbb{Q} \cup \{ +\infty \}$ or more generally on time intervals (left-closed, right-open).

  - $n$-uplet: division in $n$ equal durations  
	$d_n: D^n \to D$, $\frac{p}{q.n},...,\frac{p}{q.n} \mapsto \frac{p}{q}$  
    or $d_n: I^n \to I$, $[ a, a + \frac{b-a}{n}[, [a + \frac{b-a}{n}, a + \frac{2(b-a)}{n}[... [a+\frac{(n-1)(b-a)}{n}, b[ \to [a, b[$  
  - bar-split (binary): 1st arg. has duration 1 bar, 2d is the rest  
    $b: D^2 \to D$, $1, +\infty \mapsto +\infty$  
    or $I^2 \to I$, $[a, a+1[, [ a+1, +\infty[ \to [ a, +\infty[$  
  - ornament (binary): first argument has duration 0  
    $o: D^2 \to D$, $\frac{0}{q}, \frac{p}{q} \mapsto \frac{p}{q}$  
    or $o: I^2 \to I$, $[a, a[, [a, b[ \to [a, b[$  
  - fork : concurrent simultaneous voices  
    $f: D^2 \to D$, $\frac{p}{q}, \frac{p}{q} \to \frac{p}{q}$  
    or $f: I^2 \to I$, $[a, b[, [a, b[ \to [a, b[$ 
  - chord = special case of fork (?)

example: 
one 4/4 measure $t_0 = d_2(...)$.

For completeness, we may consider args with **multiplicity**, for the summation of siblings.

example ($N$ = note):
$d_4(N, N : 2, N)$ to represent a syncope, where the second argument has a double duration compared to 
the others.

For more examples, see 
- MCM'19 https://hal.inria.fr/hal-01988990
  version ancienne et partielle de scole model (arbres de rhythme, de syntaxe, serialization...) 
- https://gitlab.inria.fr/qparse/paper-sdags  exemples avec multiplicités


#### other optional operators 
for performance indications, control, engraving stuff, annotations (lyrics, fingering...) *etc*.

All these symbols are unary (markups). Similarly as for musical events, the temporal position of these markups follows from the embedding time operators.

  - articulation: *staccato* *etc*
  - dynamics: *p*, *f*...
  - ornament: *mordent*, *gruppetto*, *trill*...
  - bar (special mark, in addition to above *split*) 
  - *jump*...  
    about control indications, posibly paired, cf. R. Dannenberg et al. ICMC 2012.
  - fermata
  - breath
  - key change of time sigature, key, clef...
  - tempo
  - ...
 
example: two 4/4 measures ($B_2$ = double-bar):
$b(t_0, b(t_0, B_2)$.
 
example: two 2/4 measures with dynamics
($N$ = note, $B$ = blank, $P$ = piano):
$$f(b(d_2(N, N), d_2(N, N)), d_2(d_2(B, P), d_2(B, B))$$
 
We might also want to consider unary symbols 
in order to anchor explicitely an annotation to an event.

exemple: *fermata*.
  

"spanning" annotations (annotation with ha duration, like notes):

  - dynamic: "spin" *cresc* or *dim*... 
  - slur
  - trill (spanning)
  - vibrato
  - glissando
  - volta
  - octave change  (+8 etc)
  - pedal...

example: spin *cresc* during the 2 first beats of a 4/4/ bar ($F$ = forte):
$$f(d_2(d_2(N, N), d_2(N, N)), d_2(CRESC, d_2(F, B))$$


## non-ambiguity
Ideally, we need to be able to build a unique representation of a given score, to act as a reference.
In other words, we need a canonical representative for equivalent tree representation, where equivalence follows from equations like below.

$$d_2(d_3(x_1, x_2, x_3), d_3(x_4, x_5, x_6)) = 
  d_3(d_2(x_1, x_2), d_2(x_3, x_4), d_2(x_5, x_6))$$

$$f(b(x_1, y_1), b(x_2, y_2)) = b(f(x_1, x_2), f(y_1, y_2))$$

Some equations are simplifying, like ($C$ = continuation):
$$d_2(N, C) = N, \ \ \ d_2(C, C) = C$$


for more details, see
- https://hal.inria.fr/hal-01403982 (equivalent rhythm trees)
- https://hal.inria.fr/hal-01138642


For disambiguation, we may also limit the tuplets to prime numbers.
$$d_4(x_1, x_2, x_3, x_4) = d_2(d_2(x_1, x_2), d_2(x_3, x_4))$$


## linearization
for the linearization of these descriptors, see the nested words of Alur et al.


[Nested Words and Visibly Pushdown Languages](https://www.cis.upenn.edu/~alur/nw.html "https://www.cis.upenn.edu/~alur/nw.html")  
  page maintained by [Rajeev Alur](https://www.cis.upenn.edu/~alur/home.html "https://www.cis.upenn.edu/~alur/home.html")
  summary and biblio on newsted words and VPL

some docs in this repo:

- [NestedWords.md](/NestedWords) (definitions of Alur et al)
- [RhythmNestedWords.md](/RhythmNestedWords)   (an example with rhythm trees)


## languages
Several well studied formalisms (grammars and automata on tree or nested-words) 
exist for characterizing languages of syntactically well formed score representations.

(analogous of XML schemas ?)

Assuming a fixed language description (grammar or automaton), 
a score representation may be given directly as a run (of automaton) or derivation (of grammar),
for simplicity.


## exact search
Sequences of events, for building an index (e.g. n-gram based) can be extracted from nested-word representation, by projection.

Is it interesting to add the temporal markups (parentheses) in the index?

## approximated search
Does the nested-word representation allow for tractable computation of a restricted Montgeau-Sankoff edit distance?







