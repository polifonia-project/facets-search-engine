# Structure of the data indexed by Facets

## Role of Facets

Facets is centered on music content codified according to the principles of music notation, and annotated with metadata. The central notion is an *Opus*. An opus is essentially:

  - a music document from which codified music content can be extracted ; typically a MEI document containing a codified music score.
  - a set of meta-data that qualify the opus: a composer, a genre, an instrumentation, a period, etc. 
  
 At first glance, an Opus might be considered as equivalent to a music score encoded in a codified language. It is howerver at the same time more and less than that.
 
   - more : annotations can be added to the music content (for instance harmony, texture, timbre). Such annotations are distinct from the opus-level annotations: they qualify the music  at a specific musical timestamp.
   - less: Facets ignores layout instructions, such as staves, clefs, page and system breaks, etc. 
   
 Opus are organized in a hierarchy of collections (or 'Corpus').  Facets takes as input such collection, and supplies search and navigation services.
 
 ## Faceted search
 
 Facets allows search by music content in indexed collections. The result set mixes opus of many different kinds. 
 
 In order to help the user organizing, we can partition the result in subsets accordings to *facets*, i.e., properties that characterize each opus. Here is a list of possible facets:
 
   - **composer**: easy for the all:composers collection, for the other collection, the composer is anonymous
   - **period**: can be inferred from the composer birth/death.
   - **country**: again, a property of the composer
   - **genre**: here we should ask to Polifonia whether there is a well adopted list of music genre that can be used to qualify an opus (monodies, songs, quartet, symphonies, etc.)
   - **tonality**: extracted from the Opus content (shoud be done with care) ; 
   - **instrumentation**: number of parts 
   
 
