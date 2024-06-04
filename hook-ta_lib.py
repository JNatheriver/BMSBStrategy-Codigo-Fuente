from PyInstaller.utils.hooks import collect_all

datas,binaries,hiddenimports = collect_all('talib')

binaries += [(r"C:\Users\jnath\Downloads\ta-lib-0.4.0-msvc\ta-lib\swig\lib\perl\ta.dll")]