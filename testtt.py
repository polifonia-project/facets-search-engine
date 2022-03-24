import zipfile
import io
f = open("teststr.txt", "rb")
bytestr = f.read()
zf = zipfile.ZipFile(io.BytesIO(bytestr), "r")

