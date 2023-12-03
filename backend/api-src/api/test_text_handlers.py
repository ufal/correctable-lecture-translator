from text_handlers import ASRTextUnit, Timespan


def test_Timespan():
    timespan = Timespan(0, 1)

    assert timespan.start == 0.0
    assert timespan.end == 1

    # test json serialization
    json_repr = timespan.to_json()
    timespan2 = timespan.from_json(json_repr)

    assert timespan2.start == 0.0
    assert timespan2.end == 1


def test_ASRTextUnit():
    tstart = 2
    tend = 3
    asr_text = "This is some transcribed text."
    timespan = Timespan(tstart, tend)
    asr_text_unit = ASRTextUnit(text=asr_text, id_num=0, timespan=timespan, version=0)
    assert asr_text_unit.text == asr_text
    assert asr_text_unit.id_num == 0
    assert asr_text_unit.timespan.start == tstart
    assert asr_text_unit.timespan.end == tend
    assert asr_text_unit.version == 0

    print()
    print(asr_text_unit)

    # test json serialization
    json_repr = asr_text_unit.to_json()
    asr_text_unit2 = asr_text_unit.from_json(json_repr)

    assert asr_text_unit2.text == asr_text
    assert asr_text_unit2.id_num == 0
    assert asr_text_unit2.timespan.start == tstart
    assert asr_text_unit2.timespan.end == tend
    assert asr_text_unit2.version == 0
