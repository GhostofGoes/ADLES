
def test_sizeof_fmt():
    from adles.utils import sizeof_fmt
    
    assert sizeof_fmt(0) == '0.0bytes'
    assert sizeof_fmt(10.12345) == '10.1bytes'
    assert sizeof_fmt(10.19) == '10.2bytes'
    assert sizeof_fmt(1023) == '1023.0bytes'
    assert sizeof_fmt(1024) == '1.0KB'
    assert sizeof_fmt(10000) == '9.8KB'
    assert sizeof_fmt(1000000000) =='953.7MB'
    assert sizeof_fmt(100000000000000000) == '90949.5TB'
    
    #assert sizeof_fmt(None) == ''
    #assert sizeof_fmt('a') == ''
    #assert sizeof_fmt(-100000) == '-97.7KB'