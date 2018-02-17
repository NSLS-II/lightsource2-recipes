:: Doesn't include gmock or gtest. So, need to get these ourselves for `make check`.
git clone -b release-1.7.0 git://github.com/google/googlemock.git gmock
if errorlevel 1 exit 1
git clone -b release-1.7.0 git://github.com/google/googletest.git gmock/gtest
if errorlevel 1 exit 1

:: Setup directory structure per protobuf's instructions.
cd cmake
if errorlevel 1 exit 1
mkdir build
if errorlevel 1 exit 1
cd build
if errorlevel 1 exit 1
mkdir release
if errorlevel 1 exit 1
cd release
if errorlevel 1 exit 1

:: Configure and install based on protobuf's instructions and other `bld.bat`s.
cmake -G "NMake Makefiles" ^
         -DCMAKE_BUILD_TYPE=Release ^
         -DCMAKE_PREFIX_PATH=%LIBRARY_PREFIX% ^
         -DCMAKE_INSTALL_PREFIX=%LIBRARY_PREFIX% ^
         -Dprotobuf_WITH_ZLIB=ON ^
         ../..
if errorlevel 1 exit 1
nmake
if errorlevel 1 exit 1
nmake check
if errorlevel 1 exit 1
nmake install
if errorlevel 1 exit 1

:: Install the Python portions too.
cd %SRC_DIR%
if errorlevel 1 exit 1
cd python
if errorlevel 1 exit 1

:: Begin fix for missing packages issue: https://github.com/conda-forge/protobuf-feedstock/issues/40
if not exist "google/protobuf/util" mkdir "google/protobuf/util"
if errorlevel 1 exit 1
if not exist "google/protobuf/compiler" mkdir "google/protobuf/compiler"
if errorlevel 1 exit 1
type nul >> "google/protobuf/util/__init__.py"
if errorlevel 1 exit 1
type nul >> "google/protobuf/compiler/__init__.py"
if errorlevel 1 exit 1
:: End fix

"%PYTHON%" setup.py install --single-version-externally-managed --record record.txt
if errorlevel 1 exit 1
