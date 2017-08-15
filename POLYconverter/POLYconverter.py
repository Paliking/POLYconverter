import argparse
import adjust

def init_parser():
    parser = argparse.ArgumentParser(description="Spracovnie zapisnika z merania polygonoveho tahu a priprava vstupu pre program Kokes v tvare *.plx")
    parser.add_argument("input_file", help="Vstupny subor - zapisnik z merania", type=str)
    parser.add_argument("nadvys", help="Priblizna nadmorska vyska polygonoveho tahu [m]", type=float)
    parser.add_argument("opr100m", help="Oprava na 100m dlzky pri redukcii dlzok zo skreslenia pouzitej projekcie [mm] - odcitane z diagramu", type=float)
    parser.add_argument("-nor","--nie_red_dlzok", help="Redukcia dlzok sa nebude uvazovat vo vysledku", action="store_true")
    parser.add_argument("-H1","--H_first", help="Nadmorska vyska prveho stanoviska [m]", default=None, type=float)
    parser.add_argument("-H2","--H_last", help="Nadmorska vyska posledneho stanoviska [m]", default=None, type=float)
    parser.add_argument("-plxv","--plx_vysuhl", help="*.plx subor bude v tvare potrebnom na vyskove riesenie polygonu v Kokesi", action="store_true")
    args = parser.parse_args()
    return args



if __name__ == "__main__":
    args = init_parser()

    # redukcia dlzok
    if args.nie_red_dlzok:
        dist_reduce = False
    else:
        dist_reduce = True
        
    # vyskovy vypocet
    oprav_vysky = False
    if args.H_first is not None:
        comp_hights = True
        if args.H_last is not None:
            oprav_vysky = True
    else:
        comp_hights = False

    adjust.compute_measurements(args.input_file, args.nadvys, args.opr100m, dist_reduce=dist_reduce, comp_hights=comp_hights, 
                                H1=args.H_first, H2=args.H_last, oprav_vysky=oprav_vysky, plx_vysuhl=args.plx_vysuhl)