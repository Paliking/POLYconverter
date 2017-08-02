# POLYconverter
Konvertor zapisnika z merania polygonoveho tahu na format .plx pre spracovanie v Kokesi 

### Postup merania polygonoveho tahu
 - dodrzanie postupu merania polygonoveho tahu podla examples/Postup_merania.docx
 - export dat z pristroja LEICA TS15 pomocou formatovacieho suboru examples/GKUv2017.FRT
 - priklad exportnutych dat z pristroja LEICA TS15: examples/example.txt

### Vyuzitie POLYconverter.exe
 - automaticke "vystriedenie" zapisnika z merania polygonoveho tahu
 - pri merani viac ako dvoch skupin sa spriemeruju len dve "najblizsie" skupiny
 - moznost opravy meranych dlzok o redukciu z nadmorskej vysky a zo skreslenia pouzitej projekcie
 - priprava suboru vo formate .plx pre spracovanie polygonu v programe KOKES
 - vypocet vysok bodov polygonu a bodov meranych stranou

### Options
```
> POLYconverter.exe -h
usage: POLYconverter.exe [-h] [-nor] input_file nadvys opr100m

Spracovnie zapisnika z merania polygonoveho tahu a priprava vstupu pre program
Kokes v tvare *.plx

positional arguments:
  input_file            Vstupny subor - zapisnik z merania
  nadvys                Priblizna nadmorska vyska polygonoveho tahu [m]
  opr100m               Oprava na 100m dlzky pri redukcii dlzok zo skreslenia
                        pouzitej projekcie [mm] - odcitane z diagramu

optional arguments:
  -h, --help            show this help message and exit
  -nor, --nie_red_dlzok
                        Redukcia dlzok sa nebude uvazovat vo vysledku
  -H1, --H_first
                        Nadmorska vyska prveho stanoviska [m]
  -H2, --H_last
                        Nadmorska vyska posledneho stanoviska [m]
```

### Priklad1 (polohove riesenie s redukciou dlzok)
Konvertovanie zapisnika example.txt s pribliznou nadmorskou vyskou miesta merania 500m 
a koeficientom -3 odcitanom z diagramu dlzkovych oprav examples/Diagram_dlzkoveho_skreslenia.jpg
```
> POLYconverter.exe examples/example.txt 500 -3
```
Vystup su dva subory
 * **example.plx** 
	* subor na spracovanie polygonoveho tahu v programe KOKES
	* pred nacitanim do KOKESU je potrebne vypocitat smerniky zaciatocnych a koncovych bodov 
	a manualne ich doplnit do .plx suboru, pretoze konvertor nepracuje so suradnicami bodov.
	Priklad korektneho .plx suboru je examples/PLXvzor.plx (pozor na pismeno "s" pred hodnotou smernika).
 * **example_stranou.csv**
	* zoznam bodov stranou s vyslednymi Hz uhlami, zenit. uhlami, dlzkami.
	* napr. oznacenie 701-702-150 znamena uhol medzi bodmi 701-150 zo stanoviska 702 (na bod 701 je nulovy smer)

### Priklad2 (polohove riesenie bez redukcii dlzok)
Konvertovanie zapisnika example.txt bez vyuzitia redukcie dlzok. 
Po pridani prikazu --nie_red_dlzok sa nevykona redukcia meranych dlzok 
a vlozene info o vyske a koeficiente skreslenia bude ignorovane.
```
> POLYconverter.exe examples/example.txt 500 -3 --nie_red_dlzok
```

### Priklad3 (vypocet vysok)
Vypocet vysok meranych bodov pri znamej vyske prveho a posledneho stanoviska **(nie orientacie)**.
Po pridani prikazov -H1 100 -H2 200, reprezentujucich vysku 100m na prvom stanovisku 
a 200m na poslednom stanovisku polygnoveho tahu.
**Vystup** bude novy subor s nazvom **example_vysky.csv**.
Vypocita sa vyska vsetkych stanovisk od prveho az po posledne a dosiahnuta odchylka vo vyske na 
poslednom stanovisku sa rovnomerne rozrata na vsetky body polygonoveho tahu.
```
> POLYconverter.exe examples/example.txt 500 -3 -H1 100 -H2 200
```

### Priklad4 (vypocet vysok)
Vypocet vysok meranych bodov pri znamej vyske iba prveho stanoviska (napr. rajon,...).
Po pridani prikazu -H1 100, reprezentujuci vysku 100m na prvom stanovisku polygnoveho tahu.
```
> POLYconverter.exe examples/example.txt 500 -3 -H1 100
```