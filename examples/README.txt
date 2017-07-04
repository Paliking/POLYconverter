Konvertor sluzi na konvertovanie vystupu z pristroja LEICA TS15 na format *.plx, akceptovany programom KOKES na spracovavanie polygonovych tahov.

POSTUP MERANIA ktory treba dodrzat:
- metoda merania Z'Z''P''P' !!!
- jeden polygon na jednu zakazku !!!
- meranie bodov stranou najprv v I. polohe, potom v II. !!! a oznacovat rovnaky nazov bodu pre obe polohy
- meranie skupiny je ukoncene meranim na bod vpred
- najprv merat bod spat, potom body stranou, na koniec bod vpred (mozne len pri merani prvej skupiny) !!
- meranie moze mat lubovolny pocest skupin (aj jednu)
- rajon merat ako samostatny polygon v novej zakazke (prvy bod bude "bod stranou" z primarneho polygonu)




Logika konvertora pre korektne fungovanie:
- kazdy vystup merania polygonoveho tahu z LEICA TS15 zacina chybovym "prazdnym" stanoviskom.
	Toto stanovisko je ignorovane, ale pre spravnost konvertora sa v zapisniku musi nachadzat.
- Prve korektne stanovisko polygonoveho tahu ma prvu zameru v prvej polohe duplicitne a bez meranej dlzky.
	Vdaka tomu je mozne vizualne rozpoznat zaciatok polygonoveho tahu v pripade, ak sa meraci pomylili
	a nezacali novu zakazku pre novy polygonovy tah. Konvertor si automaticky poradi s duplicitnym zaciatkom, ale
	ak je v jednej zakazke/subore viac polygonov, treba ich manualne rozdelit na viac suborov.
- Posledny merany bod v bloku pre kazde stanovisko je urceny ako bod_vpred polygonoveho tahu.
	Oznacenie bodu_vpred urcuje koniec kazdej meranej skupiny. Preto je dolezite, aby kazda skupina 
	bola ukoncena meranim na bod vpred. T.j. body stranou merane pred ukoncenim skupiny.
- v kazdej skupine musi byt parny pocet merani (ak nieje, program upozorni kde je chyba)
- musi byt dodrzany rovnaky nazov bodu stranou v oboch polohach a musi sa zacat merat v prvej polohe!!!
	Program upozorni na chybu ak bod stranou nema rovnaky nazov v dvoch polohach.
	Takato kontrola nieje pri bodoch spat a vpred, nakolko nazvy su prisne kontrolovane modom merania a mali by byt korekte.
- program kontroluje poradie meranych bodov a ak bod stranou je merany na zaciatku alebo konci skupiny, upozorni chybovou hlaskou. 
	To neplati pre poslednu zostavu polygonoveho tahu, kde treba manualne skontrolovat, aby bod stranou nebol merany na konci zostavy.

Specialne rady a triky
- na konci poslednej zostavy musi byt korektna zamera vpred (ine porusenia poradia sa automaticky hlasia)
- ak sa meria dlhsi rajon (nie polygon), tak treba manualne pri poslednej zostave doplnit novy vymysleny riadok reprezentujuci zameru vpred,
kedze realne na konci rajonu neexistuje. Inak bude vo vypocte uhlov pre body stranou v rajone posledny bod stranou chybat.