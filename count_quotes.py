content = open('quality_models.py').read()
qf = 'f' + chr(34) * 3
qt = chr(34) * 3
print('f""" count:', content.count(qf))
print('""" count:', content.count(qt))