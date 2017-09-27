# Pavol Ceizel 20.6.2017
import csv
import os
import math

def get_blocks(seq):
    '''
    gets blocks of text file as generator.
    '''
    in_proces = False

    data = []
    for line in seq:
        if line.startswith('Stanovisko') and in_proces == False:
            in_proces = True

        if in_proces:
            if line.startswith('Stanovisko') and in_proces == True:
                if data:
                    yield data
                    data = []
            data.append(line.strip())
    # to get last block
    yield data


def get_measurements(file):
    '''
    Pre kazde stanovisko sa ziskaju merania zo suboru (txt vystup z LEICA TS15).

    OUTPUTS
    data_by_stanovisko: list of dics; every dict represents one stanovisko with info as
                        stanovisko, bod_spat, bod_vpred and meranie.
                        example: 
                        {'meranie': [ ('O1', 200.0023, 4.109), ('S2', 319.5672, 2.559), ('S2', 119.5631, 2.559), ...], 
                        'bod_spat': 'O1', 'bod_vpred': 'S2', 'stanovisko': 'S1'}

    '''
    data_by_stanovisko = []
    prve_stan = True

    with open(file) as obj:
        gen = get_blocks(obj)
        for block in gen:
            # first block is a bug (skip it)
            if len(block) > 8:
                # osetrenie ak je v poslednom riadku medzera/tabulator
                if len(block[-1]) == 0:
                    block = block[:-1]

                stat_data = {}
                stanovisko = block[1].split()[0]
                stat_data['stanovisko'] = stanovisko
                if prve_stan:
                    vys_stroj = float(block[1].split()[4])
                    prve_stan = False
                else:
                    vys_stroj = float(block[1].split()[6])
                stat_data['vys_stroj'] = round(vys_stroj, 3)

                spat_idx = block.index('Orientacie:')
                bod_spat = block[spat_idx+1].split()[0]
                stat_data['bod_spat'] = bod_spat

                bod_vpred = block[-1].split()[0]
                stat_data['bod_vpred'] = bod_vpred

                meranie_idx = block.index('Merane body:')

                meranie = []
                for line in block[meranie_idx+1:]:
                    splited_line = line.split()
                    ciel = splited_line[0]
                    Hz = float(splited_line[1])
                    V = float(splited_line[2])
                    # prvemu stanovisku chyba prva merana dlzka (docasne bude -1)
                    # a preto udaj o vyske zrkadla je na inom indexe
                    try:
                        vzd = float(splited_line[4])
                        vyska_zrk = float(splited_line[5])
                    except:
                        vzd = -1
                        vyska_zrk = float(splited_line[3])
                    meranie.append((ciel,Hz,vzd, V, vyska_zrk))

                stat_data['meranie'] = meranie
                data_by_stanovisko.append(stat_data)
    return data_by_stanovisko


def correct_first_stat(measurements):
    '''
    Prve stanovisko ma "bug". Prve meranie je duplicitne a chyba merana dlzka.
    Funkcia odstrani prvy riadok a doplni chybajucu dlzku skopirovanim dlzky
    z merania v druhej polohe.
    '''
    copied_distance = measurements[0]['meranie'][2][2]
    target, Hz, _, V, vys_zrk = measurements[0]['meranie'][1]
    new_entry = (target, Hz, copied_distance, V, vys_zrk)
    correct_values = measurements[0]['meranie'][2:]
    corrected_measurement = [new_entry] + correct_values
    all_measures = measurements.copy()
    all_measures[0]['meranie'] = corrected_measurement
    return all_measures


# funkcia na prevod uhla na interval 0-400
def in400(uhol):
    if uhol >= 400:
        uhol = uhol - 400
    elif uhol < 0:
        uhol = uhol + 400
    else:
        pass
    return uhol


def skupina_avg(skupina, stanovisko, cs):
    '''
    Funkcia na priemerovanie a redukovanie smerov v jednej skupine 
    
    INPUT
    skupina: list of tuples; [(ciel, Hz, vzd),...]
                musi byt parny pocet tuples tj. merany kazdy bod v dvoch polohach
    stanovisko: str; nazov stanoviska
    cs: int; poradove cislo skupiny od 0

    OUTPUTS
    measure_AVGed: list of tuples;
                [(ciel, Hz, vzd),...] spriemerovane smery z 2 poloh a 
                zredukovane na nulovu orientaciu
    '''
    smery = [] # hz
    dlzky = []
    ciele = []
    zenit_uhl = []
    vysky_zrk = []
    last_idx = len(skupina) - 2
    # loop throught each target
    for i in range(0,len(skupina),2):
        name1 = skupina[i][0]
        name2 = skupina[i+1][0]
        if not name1 == name2:
            error_message = '''
            'Vyskytol sa problem v skupine cislo {} pre stanovisko {}. Priemerovana zamera 
            v prvej a druhej polohe ma iny nazov bodu ({} a {}). Oprav manualne zapisnik!!!'     
            '''.format(cs+1, stanovisko, name1, name2)
            raise ValueError(error_message)

        if i == last_idx:
            Hz_p2 = skupina[i][1]
            Hz_p1 = skupina[i+1][1]
            V_p2 = skupina[i][3]
            V_p1 = skupina[i+1][3]
        else:
            Hz_p1 = skupina[i][1]
            Hz_p2 = skupina[i+1][1]
            V_p1 = skupina[i][3]
            V_p2 = skupina[i+1][3]

        dlzka1 =  skupina[i][2]
        dlzka2 =  skupina[i+1][2]
        dlzky.append(round((dlzka1 + dlzka2)/2,3))

        Hz_p1 = in400(Hz_p1)
        Hz_p2_cor = in400(Hz_p2 - 200)
        # osetrenie prechodu cez 0.0000
        if round(Hz_p1) == round(Hz_p2_cor):
            smer = (Hz_p1 + Hz_p2_cor)/2
        else:
            smer = (Hz_p1 + Hz_p2_cor + 400)/2
            smer = in400(smer)

        zenit_uhl.append(round((400 + V_p1 - V_p2)/2, 4))
        smery.append(smer)
        ciele.append(skupina[i][0])

        vys_zrk = skupina[i][4]
        vysky_zrk.append(vys_zrk)

    # redukovane smery
    smery_red = [ round(in400(s-smery[0]),4) for s in smery ]
    measure_AVGed = []
    for i in range(int(len(skupina)/2)):
        measure_AVGed.append((ciele[i], smery_red[i], dlzky[i], zenit_uhl[i], vysky_zrk[i]))
    
    return measure_AVGed
        

def AVG_tuples(*tuples):
    '''
    AVG second and third element in tuples.
    First element must be the same.
    AVG_tuples(('bod', 50, 20), ('bod', 50, 30)) --> ('bod', 50, 25)
    '''
    n_tuples = len(tuples)
    names = [ tup[0] for tup in tuples]
    Hz_sum = sum([ tup[1] for tup in tuples])
    vzd_sum = sum([ tup[2] for tup in tuples])
    V_sum = sum([ tup[3] for tup in tuples])
    vys_zrk = tuples[0][4]
    if len(set(names)) == 1:
        name = names[0]
        Hz = round((Hz_sum)/n_tuples, 4)
        vzd = round((vzd_sum)/n_tuples, 3)
        V = round((V_sum)/n_tuples, 4)
        tuple_AVG = (name, Hz, vzd, V, vys_zrk)
    else:
        raise ValueError('Rozne body sa nesmu priemerovat!!!')
    return tuple_AVG


def best_two(diffs):
    '''
    Find indices of the best two groups with similar angles.

    INPUT
    diffs: list of floats; It represents an angle difference for each group from their mean.

    OUTOUT
    best_groups_idx: tuple woth two integers; indices of groups with the most similar angles.
    '''
    residuals = []
    # kontroluju sa iba kombinacie
    for i, diff_curr in enumerate(diffs):
        if i == len(diffs) - 1:
            break
        diff_rest = diffs[i+1:]
  
        diffs_betw_two = [abs(diff-diff_curr) for diff in diff_rest ]
        idx_part, res = min(enumerate(diffs_betw_two))
        idx_orig = idx_part + i + 1
        residuals.append((res, (i, idx_orig)))
    best_groups_idx = min(residuals)[1]
    return best_groups_idx


def adjust_zostava(zostava):
    '''
    Ziskanie priemernych smerov a dlzok z dvoch najpodobnejsich skupin (blizky Hz) pre jednu zostavu.

    INPUT
    zostava: dict; data pre jednu zostavu/stanovisko;
                    priklad: {'meranie': [ ('O1', 200.0023, 4.109), ('S2', 319.5672, 2.559), ('S2', 119.5631, 2.559), ...], 
                            'bod_spat': 'O1', 'bod_vpred': 'S2', 'stanovisko': 'S1'};
                    tuples obsahuju 3 prvky -  (stanovisko, Hz uhol, vzdialenost)

    OUTPUT
    zostava_output: dict; Vysledne priemerne smery na stanovisku
                    examle:     {'stanovisko': {'name': 'S3'}, 'bod_vpred': {'name': 'O2', 'data': ('O2', 395.86, 4.457)}, 
                                    'stranou': {'name': [], 'data': []}}
    '''
    AVGs_in_groups = [] # zamery z kazdej skupiny (uz spriemerovane dve polohy...)
    zostava_output = {}
    zamery_stranou = []
    stanovisko = zostava['stanovisko']
    bod_spat = zostava['bod_spat']
    bod_vpred = zostava['bod_vpred']
    vys_stroj = zostava['vys_stroj']
    # indices of bod_vpred's measurements
    vpred_idxs = [i for i, mer in enumerate(zostava['meranie']) if mer[0]==bod_vpred ]
    # koncove indexy kazdej skupiny (skupina konci druhym meranim bodu vpred)
    skupiny_idxs = vpred_idxs[1::2]
    n_skupin = len(skupiny_idxs)
    # cyklus cez skupiny
    for j, end_idx in enumerate(skupiny_idxs):
        if j == 0:
            skupina_data = zostava['meranie'][:end_idx+1]
        else:
            start_idx = skupiny_idxs[j-1]+1
            skupina_data = zostava['meranie'][start_idx:end_idx+1]

        if not len(skupina_data) % 2 == 0:
            raise ValueError('Skupina cislo {} pre stanovisko {} nema parny pocet zamer. Oprav manualne zapisnik!!!'.format(j+1, stanovisko))
        # Spriemerovane dve polohy a redukcia orientacie v ramci jednej skupiny
        AVG_in_group = skupina_avg(skupina_data, stanovisko, j)
        # get all body stranou
        for zamera in AVG_in_group:
            if zamera[0] not in [bod_spat, bod_vpred]:
                zamery_stranou.append(zamera)

        AVGs_in_groups.append(AVG_in_group)

    # Hladanie dvoch najvhodnejsich skupin a finalne spriemerovanie uhlov z tychto skupin
    # Priemeruje sa len zamera vpred. Body stranou su merane len v jednej skupine.
    # ak je pocet skupin dva a viac
    if len(AVGs_in_groups) > 1:
        zamery_vpred = [ gr[-1] for gr in AVGs_in_groups]
        # priemer zo vsetkych skupin
        AVGed_all_groupes = AVG_tuples(*zamery_vpred)
        # rozdiely uhlov voci priemeru
        difs = [round(zamera_vpred[1] - AVGed_all_groupes[1], 4) for zamera_vpred in zamery_vpred]
        # najdenie dvoch najpodobnejsich rozdielov uhlov voci priemeru
        best_groups_idx = best_two(difs)
        # spriemerovanie dvoch najvhodnejsich skupin
        idx_first = best_groups_idx[0]
        idx_second = best_groups_idx[1]
        first_gr_vpred = AVGs_in_groups[idx_first][-1]
        second_gr_vpred = AVGs_in_groups[idx_second][-1]
        AVGed_two_groupes_vpred = AVG_tuples(first_gr_vpred, second_gr_vpred)
        first_gr_vzad = AVGs_in_groups[idx_first][0]
        second_gr_vzad = AVGs_in_groups[idx_second][0]
        AVGed_two_groupes_vzad = AVG_tuples(first_gr_vzad, second_gr_vzad)
    # ak je iba jedna skupina
    else:
        AVGed_two_groupes_vpred = AVGs_in_groups[0][-1]
        AVGed_two_groupes_vzad = AVGs_in_groups[0][0]

    zostava_output['stanovisko'] = {'name': stanovisko, 'vys_stroj': vys_stroj}
    zostava_output['bod_vpred'] = {'name': bod_vpred, 'data': AVGed_two_groupes_vpred}
    zostava_output['bod_spat'] = {'name': bod_spat, 'data': AVGed_two_groupes_vzad}
    body_stranou = [ point for point, *_ in zamery_stranou]
    zostava_output['stranou'] = {'name': body_stranou, 'data': zamery_stranou}
    return zostava_output


def write_plx(file, zostavy, vysk_uhly=False):
    '''
    Ulozi data do plx subor, co je vstupny format pre vypocet polygonu pre kokes.

    INPUTS
    file: str; save output to this file
    zostavy: dict; spriemerovane uhly na kazdom stanovisku;
            example: {'stanovisko': {'name': 'S3'}, 'stranou': {'name': [], 'data': []}, 
                    'bod_spat': {'name': 'S2', 'data': ('S2', 0.0, 2.885)}, 
                    'bod_vpred': {'name': 'O2', 'data': ('O2', 395.86, 4.457)}}
    vysk_uhly: bool; Ak True, tak je pridany dalsi stlpec s vyskovymi uhlami a
                zmeni sa hlavicka suboru plx. Vyuziva sa to pri vyskovom rieseni  
                polygonu v Kokesi.
    '''
    # write to file
    with open(file, 'w', newline='') as plxfile:
        plxriter = csv.writer(plxfile, delimiter=' ',
                                quoting=csv.QUOTE_MINIMAL)
        # first two rows
        if vysk_uhly:
            plxriter.writerow(['//', 'vysky=1', 'delky=0', 'zenit=-1', 'cnt_poc=1', 'cnt_kon=1'])
        else:
            plxriter.writerow(['//', 'vysky=0', 'delky=0', 'zenit=-1', 'cnt_poc=1', 'cnt_kon=1'])
        orientacia1 = zostavy[0]['bod_spat']['name']
        stanovisko1 = zostavy[0]['stanovisko']['name']
        plxriter.writerow(['smernik {}-{}'.format(stanovisko1, orientacia1)])

        # vsetky stanoviska okrem posledneho
        for i, zost in enumerate(zostavy[:-1]):
            # sucastne stanovisko
            stanovisko = zost['stanovisko']['name']
            Hz_vpred = zost['bod_vpred']['data'][1]
            vzd_vpred = zost['bod_vpred']['data'][2]
            # vzdialenost spat z dalsieho stanoviska (ta ista vzdialenost)
            next_vzd_spat = zostavy[i+1]['bod_spat']['data'][2]
            AVG_vzd = round((vzd_vpred + next_vzd_spat) / 2, 3)
            if not vysk_uhly:
                plxriter.writerow([stanovisko, Hz_vpred, AVG_vzd])
            else:
                v_uhol_vpred = round(100 - zost['bod_vpred']['data'][3], 4)
                plxriter.writerow([stanovisko, Hz_vpred, AVG_vzd, v_uhol_vpred])

        # posledne stanovisko
        orientacia_last = zostavy[-1]['bod_vpred']['name']
        stanovisko_last = zostavy[-1]['stanovisko']['name']
        Hz_vpred = zostavy[-1]['bod_vpred']['data'][1]
        plxriter.writerow([stanovisko_last, Hz_vpred, '*'])
        # smernik na orientaciu
        plxriter.writerow(['smernik {}-{}'.format(stanovisko_last, orientacia_last)])


def red_dlzok(s, H, o):
    '''
    Redukcia vodorovnej dlzky z nadmoreskej vysky a zo skreslenia pouzitej projkcie.
    s: float; vodorovna dlzka (m)
    H: float; nadmorska vyska (m)
    o: float; oprava pre 100m dlzky odcitana z diagramu dlzkovych oprav (mm)
    K1: redukcia z nadm vysky(m)
    K2: redukcia zo skreslenia (m)
    '''
    # redukcia z nadm. vysky
    R = 6381 # km
    K1 = -H/R*s / 1000
    # redukcia zo skreslenia
    K2 = s/100*o / 1000
    return K1 + K2


def make_reductions(zostavy, H, o):
    '''
    Redukcie dlzok z nadmoreskej vysky a zo skreslenia pouzitej projkcie.

    zostavy: dict; spriemerovane uhly na kazdom stanovisku;
            example: {'stanovisko': {'name': 'S3'}, 'stranou': {'name': [], 'data': []}, 
                    'bod_spat': {'name': 'S2', 'data': ('S2', 0.0, 2.885)}, 
                    'bod_vpred': {'name': 'O2', 'data': ('O2', 395.86, 4.457)}}
    H: float; priblizna nadmorska vyska polygonoveho tahu.
    o: float; oprava pre 100m dlzky odcitana z diagramu dlzkovych oprav (mm)
    '''
    zostavy_all = zostavy.copy()
    for i, zostava in enumerate(zostavy):
        bod_vp, hz_vp, s_vp, V_vp, vys_zrk_vp = zostava['bod_vpred']['data']
        K = red_dlzok(s_vp, H, o)
        zostavy_all[i]['bod_vpred']['data'] = (bod_vp, hz_vp, round(s_vp+K, 3), V_vp, vys_zrk_vp)

        bod_vz, hz_vz, s_vz, V_vz, vys_zrk_vz = zostava['bod_spat']['data']
        K = red_dlzok(s_vz, H, o)
        zostavy_all[i]['bod_spat']['data'] = (bod_vz, hz_vz, round(s_vz+K, 3), V_vz, vys_zrk_vz)
        data_stranou = zostava['stranou']['data']
        if len(data_stranou) > 0:
            data_stranou_corr = []
            for zamera in data_stranou:
                bod, hz, s, V, vys_zrk = zamera
                K = red_dlzok(s, H, o)
                data_stranou_corr.append((bod, hz, round(s+K, 3), V, vys_zrk))
            zostavy_all[i]['stranou']['data'] = data_stranou_corr
    return zostavy_all


def write_body_stranou(file, zostavy):
    '''
    Do osobitneho suboru zapise spriemerovane uhly a dlzky pre body stranou
    '''
    with open(file, 'w', newline='') as obj:
        obj.write('Data pre body stranou\n')
        datwriter = csv.writer(obj, delimiter=',',
                                quoting=csv.QUOTE_MINIMAL)
        datwriter.writerow(['---------------------'])
        datwriter.writerow(['vzad_stan_ciel', 'Hz(g)', 'vzd(m)', 'zenit(g)'])
        for zost in zostavy:
            bod_vzad = zost['bod_spat']['name']
            stanovisko = zost['stanovisko']['name']
            for zam_stran in zost['stranou']['data']:
                bod_stranou = zam_stran[0]
                Hz_stranou = zam_stran[1]
                vzd_stranou = zam_stran[2]
                zenit_ang = zam_stran[3]
                angle_mark = '{}-{}-{}'.format(bod_vzad, stanovisko, bod_stranou)
                datwriter.writerow([angle_mark, Hz_stranou, vzd_stranou, zenit_ang])


def check_names_bodvpred(zostavy):
    '''
    Kontrola ci nazov stanoviska sa zhoduje s nazvom bodu vpred predchadzajucej zostavy.
    To znamena, ze sa kontroluje, ci nahodou niesu body stranou umiestnene omylom na konci skupiny.
    Tato kontrola sa netyka poslednej zostavy.
    '''
    last_bod_vpred = None
    for zostava in zostavy:
        stanovisko = zostava['stanovisko']
        bod_vpred = zostava['bod_vpred']
        if last_bod_vpred is None:
            last_bod_vpred = bod_vpred
            continue
        else:
            if stanovisko == last_bod_vpred:
                last_bod_vpred = bod_vpred
            else:
                error_message = '''
                Nazov stanoviska {} sa nezhoduje s nazvom zamery vpred pri 
                predchadzajucom stanovisku. Zmen zapisnik manualne!!!
                Pravdepodobne su na konci poslednej skupiny predchadzajuceho 
                stanoviska merane body stranou.'''.format(stanovisko)
                raise ValueError(error_message)


def check_names_stranou(zostavy):
    '''
    Kontrola, ci sa body stranou nenachadzaju na zaciatku alebo na konci meranej skupiny.
    Ci sa nachadzaju na konci celej zostavy riesi funkcia check_names_bodvpred (okrem poslednej zostavy, 
    tam to treba skontrolovat manualne). Tato funkcia vyzaduje, aby posledna zamera  najprv overenie spravnosti 
    funkciou check_names_bodvpred.
    '''
    for zostava in zostavy:
        stanovisko = zostava['stanovisko']
        bod_vpred = zostava['bod_vpred']
        bod_spat = zostava['bod_spat']
        body_stranou = [ zamera[0] for zamera in zostava['meranie'] ]
        indices_spat = [i for i, bod in enumerate(body_stranou) if bod == bod_spat]
        indices_vpred = [i for i, bod in enumerate(body_stranou) if bod == bod_vpred]

        indices_spat_left = indices_spat[::2]
        indices_vpred_right = indices_vpred[1::2]
        # i_spat musi byt vzdy o jedna vacsi ako i_vpred aby nebola medzi nimi medzera (vyskyt bodu stranou)
        for i_spat, i_vpred in zip(indices_spat_left[1:], indices_vpred_right[:-1]):
            if not i_spat == (i_vpred+1):
                error_message = '''
                Pri zostave na stanovisku {} sa pravdepodobne vyskytuju body stranou merane na zaciatku alebo 
                konci skupiny. Zmen zapisnik manualne, aby boli v strede skupiny!!!
                Je taktiez mozne, ze sa v skupine nachadza bod vpred viackrat (chybne merany ako bod stranou)'''.format(stanovisko)
                raise ValueError(error_message)


def elev_2points(ha, hb, alfa, s, mode='grad'):
    '''
    Vypocet prevysenia medzi bodmi AB: dH_ab = H_b - H_a

    ha - vyska stroja na bode A
    hb - vyska zrkadla na bode B
    alfa - vyskovy uhol na stanovisku A
    s - vodorovna dlzka A-B
    mode - str; 'deg', 'rad', 'grad'; jednotky vstupneho uhlu alfa
    '''
    if mode == 'deg':
        angle = math.radians(alfa)
    elif mode == 'rad':
        angle = alfa
    elif mode == 'grad':
        angle = alfa/400*2*math.pi
    else:
        raise ValueError('Uhlova jednotka {} je neznama'.format(mode))
    dH_ab = ha + math.tan(angle) * s - hb
    return dH_ab


def calc_elevations(zostavy_AVGed):
    '''
    Vypocet prevyseni stanovisko-ciel a ich pridanie do vstupneho dict.
    '''
    zostavy_new = zostavy_AVGed.copy()
    for i, zostava in enumerate(zostavy_AVGed):
        name_stroj = zostava['stanovisko']['name']
        name_ciel = zostava['bod_vpred']['name']
        h_stroj = zostava['stanovisko']['vys_stroj']
        vzd_vodor = zostava['bod_vpred']['data'][2]
        h_zrk = zostava['bod_vpred']['data'][4]
        zenit_zrk = zostava['bod_vpred']['data'][3]
        vysk_uhol = 100 - zenit_zrk
        elev = elev_2points(h_stroj, h_zrk, vysk_uhol, vzd_vodor, mode='grad')
        zostavy_new[i]['bod_vpred']['prevysenie'] = round(elev,3)
        elevations_str = []
        for zamera in zostava['stranou']['data']:
            h_zrk_str = zamera[4]
            vysk_uhol_str = 100 - zamera[3]
            vzd_vodor_str = zamera[2]
            elev_str = elev_2points(h_stroj, h_zrk_str, vysk_uhol_str, vzd_vodor_str, mode='grad')
            elevations_str.append(round(elev_str,3))
        zostavy_new[i]['stranou']['prevysenie'] = elevations_str
    return zostavy_new


def elevs2hight(elevations, H1):
    '''
    Vypocet vysok stanovisk polygonoveho tahu
    elevations: list s prevyseniami
    H1: float; vyska prveho stanoviska
    '''
    hights = []
    vyska = H1
    for elevation in elevations:
        vyska = vyska + elevation
        hights.append(round(vyska,3))
    return hights


def calc_hights(zostavy_AVGed, H1, H2=None, oprav_vysky=True):
    '''
    Vypocet vysok bodov polygonu a bodov stranou.

    OUTPUTS
    zostavy_new: rovnaky tvar ako zostavy_AVGed, ale doplneny o vysky bodov
    rozdiel: rozdiel vysky na poslednom stanovisku polygonu (znama - vypocitana) [m]
    '''
    # prevysenia a vysky pre vsetky body_vpred okrem posledneho t.j. poslednej orientacie.
    elevs = [ i['bod_vpred']['prevysenie'] for i in zostavy_AVGed[:-1] ]
    hights = elevs2hight(elevs, H1)
    rozdiel = None
    if H2 is not None:
        # rozdiel vysok na poslednom stanovisku (znama - vypocitana)
        rozdiel = round(H2 - hights[-1], 3)
    if oprav_vysky and H2 is None:
        raise ValueError('Nieje mozne opravit vysky stanovisk, ked nebola zadana vyska posledneho stanoviska')

    if oprav_vysky:
        oprava = rozdiel/len(elevs)
        elevs_corrected = [ e+oprava for e in elevs]
        hights = elevs2hight(elevs_corrected, H1)

    # zapis vysok stanovisk a bodov stranou
    zostavy_new = zostavy_AVGed.copy()
    for i, zostava in enumerate(zostavy_AVGed):
        if i == 0:
            H_stan = H1
        else:
            H_stan = hights[i-1]
        zostavy_new[i]['stanovisko']['vyska'] = H_stan
        # urcenie vysok bodov stranou
        vyska_str = []
        for prev in zostava['stranou']['prevysenie']:
            H_str = round(H_stan + prev, 3)
            vyska_str.append(H_str)
        zostavy_new[i]['stranou']['vyska'] = vyska_str
    return zostavy_new, rozdiel


def write_hights(file, zostavy, H_error, hights_fixed):
    '''
    H_error: None or float; rozdiel vypocitanej a znamej vysky na poslednom stanovisku.
    hights_fixed: bool; boli/neboli opravene vysky na stanoviskach polygonu
    '''     
    with open(file, 'w', newline='') as obj:
        if H_error is not None:
            obj.write('Rozdiel vypocitanej a znamej vysky na poslednom stanovisku je: {}m\n'.format(H_error))
        if hights_fixed:
            obj.write('Vysky bodov polygonu BOLI opravene o tento rozdiel. \n')
        else:
            obj.write('Vysky bodov polygonu NEBOLI opravene o rozdiel vysok na poslednom stanovisku. \n')
        obj.write('--------------------\n')
        datwriter = csv.writer(obj, delimiter=',',
                                quoting=csv.QUOTE_MINIMAL)
        datwriter.writerow(['bod', 'H'])
        for zost in zostavy:
            stanovisko = zost['stanovisko']['name']
            stan_hight = zost['stanovisko']['vyska']
            datwriter.writerow([stanovisko, stan_hight])
            for bod_stran, H_stran in zip(zost['stranou']['name'], zost['stranou']['vyska']):
                datwriter.writerow([bod_stran, H_stran])


def write_stanovisko(obj, name, code, vyska_stroj):
    new_line = '1 {:>12} {} {:.4f}\n'.format(name, code, vyska_stroj)
    obj.write(new_line)


def write_ciel(obj, name, vzd, vys_ciel, Hz, zenit, stranou=False):
    if stranou:
        new_line = '{:>12} {:>10.5f} {:.4f} {:>10.6f} {:>10.6f} R\n'.format(name, vzd, vys_ciel, Hz, zenit)
    else:
        new_line = '{:>12} {:>10.5f} {:.4f} {:>10.6f} {:>10.6f}\n'.format(name, vzd, vys_ciel, Hz, zenit)
    obj.write(new_line)


def write_zap(file, zostavy):
    '''Tvorba *.zap suboru pre spracovanie v kokesi.'''
    with open(file, 'w', newline='') as obj:
        for zost in zostavy:
            # bod spat
            bod_vzad, hz_vzad, vzd_vzad, zenit_vzad, vysk_vzad = zost['bod_spat']['data']
            # stanovisko
            stanovisko = zost['stanovisko']['name']
            vys_stroj = zost['stanovisko']['vys_stroj']
            write_stanovisko(obj, stanovisko, 0, vys_stroj)
            write_ciel(obj, bod_vzad, vzd_vzad, vysk_vzad, hz_vzad, zenit_vzad)
            obj.write('-1\n')
            # body stranou
            for zam_stran in zost['stranou']['data']:
                bod_stran, Hz_stran, vzd_stran, zenit_stran, vysk_stran = zam_stran
                write_ciel(obj, bod_stran, vzd_stran, vysk_stran, Hz_stran, zenit_stran, stranou=True)
            # bod vpred
            bod_vpred, hz_vpred, vzd_vpred, zenit_vpred, vysk_vpred = zost['bod_vpred']['data']
            write_ciel(obj, bod_vpred, vzd_vpred, vysk_vpred, hz_vpred, zenit_vpred)
            obj.write('/\n')
        obj.write('-2\n')  


def compute_measurements(file, H, o, dist_reduce=True, comp_hights=True, H1=None, H2=None,
                        oprav_vysky=True, plx_vysuhl=False):
    '''
    file: str; zapisnik z merania (.txt)
    H: float; priblizna nadmorska vyska polygonoveho tahu (kvoli redukcii dlzok).
    o: float; oprava pre 100m dlzky odcitana z diagramu dlzkovych oprav (mm)
    dist_reduce: bool; opravit dlzky o redukcie
    comp_hights: bool; Vypocet prevyseni a vysok bodov.
    H1: None or flaot; Presna vyska prveho stanoviska polygonoveho tahu ak ide o vyskove riesenie.
    H2: None or flaot; Presna vyska posledneho stanoviska polygonoveho tahu ak ide o vyskove riesenie.
    oprav_vysky: bool; Ak True a ked je definovana H1 aj H2, tak sa rozdiel vysky na poslednom stanovisku 
                    (definovana - vypocitana) rovnomerne rozdeli na vsetky stanoviska polygonu.
    plx_vysuhl: bool; Ak True, tak subor plx bude obsahovat aj vyskove uhly, potrebne na vyskove spracovanie
                    polygonu v Kokesi. Zmenena je aj hlavicka suboru plx oproti polohovemu rieseniu.

    '''
    file_base = os.path.basename(file)
    file_name = os.path.splitext(file_base)[0] # no ext.
    measures = get_measurements(file)
    measures = correct_first_stat(measures)
    check_names_bodvpred(measures)
    check_names_stranou(measures)
    # Priemerovanie zamer z dvoch najspolahlivejsich skupin.
    zostavy_AVGed = []
    for zostava in measures:
        zostava_AVGed = adjust_zostava(zostava)
        zostavy_AVGed.append(zostava_AVGed)
    # redukcie dlzok
    if dist_reduce:
        zostavy_AVGed = make_reductions(zostavy_AVGed, H, o)
    # vypocet vysok
    if comp_hights:
        zostavy_AVGed = calc_elevations(zostavy_AVGed)
        zostavy_AVGed, H_error = calc_hights(zostavy_AVGed, H1, H2=H2, oprav_vysky=oprav_vysky)
        write_hights(file_name+'_vysky.csv', zostavy_AVGed, H_error=H_error, hights_fixed=oprav_vysky)
    # write plx and body_stranou
    write_plx(file_name+'.plx', zostavy_AVGed, vysk_uhly=plx_vysuhl)
    write_body_stranou(file_name+'_stranou.csv', zostavy_AVGed)
    write_zap(file_name+'.ZAP', zostavy_AVGed)



if __name__ == '__main__':
    compute_measurements(r'..\examples\example.txt', 348, -8, H1=348.96, H2=400)
