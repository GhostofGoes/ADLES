
def test_sizeof_fmt():
    from adles.utils import sizeof_fmt

    assert sizeof_fmt(0) == '0.0bytes'
    assert sizeof_fmt(10.12345) == '10.1bytes'
    assert sizeof_fmt(10.19) == '10.2bytes'
    assert sizeof_fmt(1023) == '1023.0bytes'
    assert sizeof_fmt(1024) == '1.0KB'
    assert sizeof_fmt(10000) == '9.8KB'
    assert sizeof_fmt(1000000000) == '953.7MB'
    assert sizeof_fmt(100000000000000000) == '90949.5TB'


def test_pad():
    from adles.utils import pad

    assert pad(0) == "00"
    assert pad(5) == "05"
    assert pad(9, 3) == "009"
    assert pad(value=10, length=4) == "0010"
    assert pad(50, 5) == "00050"


def test_split_path():
    # from adles.utils import split_path
    # TODO: fix case-sensitivity on Windows!
    # assert split_path('/path/To/A/file') == (['path', 'To', 'A'], 'file')
    # TODO: fix
    # assert split_path('') == ([''], '')
    # TODO: fix
    # assert split_path('/') == (['', ''], '')
    pass


def test_get_vlan():
    # from adles.utils import get_vlan
    # todo: fix "'>=' not supported between instances of 'generator' and 'int"
    # assert get_vlan() >= 2000
    # assert get_vlan() <= 4096
    pass


def test_read_json():
    from adles.utils import read_json

    # assert isinstance(read_json('../users.json'), dict)
    assert read_json('lame.jpg') is None
