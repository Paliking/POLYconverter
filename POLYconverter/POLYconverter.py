import argparse
import adjust

def init_parser():
    parser = argparse.ArgumentParser(description="Spracovnie zapisnika z merania polygonoveho tahu a priprava vstupu pre program Kokes v tvare *.plx")
    parser.add_argument("input_file", help="Vstupny subor - zapisnik z merania", type=str)
    parser.add_argument("nadvys", help="Priblizna nadmorska vyska polygonoveho tahu [m]", type=float)
    parser.add_argument("opr100m", help="Oprava na 100m dlzky pri redukcii dlzok zo skreslenia pouzitej projekcie [mm] - odcitane z diagramu", type=float)
    parser.add_argument("--nie_red_dlzok", help="Redukcia dlzok sa nebude uvazovat vo vysledku", action="store_true")
    args = parser.parse_args()
    return args



if __name__ == "__main__":
    args = init_parser()

    if args.nie_red_dlzok:
        dist_reduce = False
    else:
        dist_reduce = True

    adjust.compute_measurements(args.input_file, args.nadvys, args.opr100m, dist_reduce=dist_reduce)