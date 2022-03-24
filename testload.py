import music21
converter"data/test2.abc"
handler = abcFormat.ABCHandler()
handler.process(score)
m21_score = m21.abcFormat.translate.abcToStreamScore(handler)
