# katalixia
A python lib that uses Espeak's phonemic decomposition to get a rime

## Install
Katalixia hasn't been posted to the pypi repo, but you should be able to install it using 

`pip3 install https://github.com/hadware/katalixia`

Dependencies (actually only the python3 lib `voxpopuli` are required, but that shouldn't be a problem since pip takes care of dependencies by itself. Be sure to install voxpuloli's dependencies, especialy the Mbrola voices.

## Usage
Basically, feed words/phrases to a `RhymeTree` object, and then ask for rhymes using the `find_rhymes` method:

```python
>>> from katalixia import RhymeTree
>>> tree = RhymeTree.from_word_list(["marteau", "bateau", "apollo", "polo", "rire", "avenir", "sourire"])
>>> tree.find_rhyme("gateau")
'bateau'
>>> tree.find_rhyme("picolo")
'polo'
```

*Examples are in French because rhymes are prettier in French. Anyone disagreeing with that shall duel me in a one-to-one joust of poetry. **The RhymeTree can however be set to use the phonemic transformation for other barbarian languages, such as German, Spanish, or even English (or any language supported by Espeak, for that matter** *

```python
>>> # at one point there should be an example here. For the time being, delight yourself witht the view of this comment
```

It's also possible to pickle and save a RhymeTree for future use (and it's even encouraged, as building the RhymeTree is a bit slow, because everything is running on your own machine and not some Silicon Valley's cloud-based docker microservice hydro-cooled hypersecured datacenter. 

```python
>>> tree.save("rhymetree.pckl")
>>> same_tree = RhymeTree.from_pickle("rhymetree.pckl") # amazingly once unpickled, it works exactly the same as it used to.
```
