make_exe:
	C:\Python34\Scripts\pyinstaller --onefile POLYconverter\POLYconverter.py
	if not exist dist\examples (mkdir dist\examples)
	COPY "README.md" "dist/examples/"
	COPY examples\* "dist\examples\"
	MOVE "dist\examples\spusti.bat" "dist\spusti.bat"
	RENAME "dist" "Polyconverter_v1.x"
	DEL "POLYconverter.spec"
	RMDIR "build" /S /Q

grip:
	C:\Python34\Scripts\grip -b