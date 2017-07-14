# Pavol Ceizel 20.6.2017
import csv
import os


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
                    # prvemu stanovisku chyba prva merana dlzka (docasne bude -1)
                    try:
                        vzd = float(splited_line[4])
                    except:
                        vzd = -1
                    meranie.append((ciel,Hz,vzd))

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
    target, Hz, _ = measurements[0]['meranie'][1]
    new_entry = (target, Hz, copied_distance)
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
    smery = []
    dlzky = []
    ciele = []
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
        else:
            Hz_p1 = skupina[i][1]
            Hz_p2 = skupina[i+1][1]

        Hz_p1 = in400(Hz_p1)

        dlzka1 =  skupina[i][2]
        dlzka2 =  skupina[i+1][2]
        dlzky.append(round((dlzka1 + dlzka2)/2,3))
        # korigovana druha poloha
        Hz_p2_cor = in400(Hz_p2 - 200)

        # osetrenie prechodu cez 0.0000
        if round(Hz_p1) == round(Hz_p2_cor):
            smer = (Hz_p1 + Hz_p2_cor)/2
        else:
            smer = (Hz_p1 + Hz_p2_cor + 400)/2
            smer = in400(smer)

        smery.append(smer)
        ciele.append(skupina[i][0])

    # redukovane smery
    smery_red = [ round(in400(s-smery[0]),4) for s in smery ]
    measure_AVGed = []
    for i in range(int(len(skupina)/2)):
        measure_AVGed.append((ciele[i], smery_red[i], dlzky[i]))
    
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
    if len(set(names)) == 1:
        name = names[0]
        Hz = round((Hz_sum)/n_tuples, 4)
        vzd = round((vzd_sum)/n_tuples, 3)
        tuple_AVG = (name, Hz, vzd)
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

    zostava_output['stanovisko'] = {'name': stanovisko}
    zostava_output['bod_vpred'] = {'name': bod_vpred, 'data': AVGed_two_groupes_vpred}
    zostava_output['bod_spat'] = {'name': bod_spat, 'data': AVGed_two_groupes_vzad}
    body_stranou = [ point for point, *_ in zamery_stranou]
    zostava_output['stranou'] = {'name': body_stranou, 'data': zamery_stranou}
    return zostava_output


def write_plx(file, zostavy):
    '''
    Ulozi data do plx subor, co je vstupny format pre vypocet polygonu pre kokes.

    INPUTS
    file: str; save output to this file
    zostavy: dict; spriemerovane uhly na kazdom stanovisku;
            example: {'stanovisko': {'name': 'S3'}, 'stranou': {'name': [], 'data': []}, 
                    'bod_spat': {'name': 'S2', 'data': ('S2', 0.0, 2.885)}, 
                    'bod_vpred': {'name': 'O2', 'data': ('O2', 395.86, 4.457)}}
    '''
    # write to file
    with open(file, 'w', newline='') as plxfile:
        plxriter = csv.writer(plxfile, delimiter=' ',
                                quoting=csv.QUOTE_MINIMAL)
        # first two rows
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
            plxriter.writerow([stanovisko, Hz_vpred, AVG_vzd])
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
        bod_vp, hz_vp, s_vp = zostava['bod_vpred']['data']
        K = red_dlzok(s_vp, H, o)
        zostavy_all[i]['bod_vpred']['data'] = (bod_vp, hz_vp, round(s_vp+K, 3))

        bod_vz, hz_vz, s_vz = zostava['bod_spat']['data']
        K = red_dlzok(s_vz, H, o)
        zostavy_all[i]['bod_spat']['data'] = (bod_vz, hz_vz, round(s_vz+K, 3))
        data_stranou = zostava['stranou']['data']
        if len(data_stranou) > 0:
            data_stranou_corr = []
            for zamera in data_stranou:
                bod, hz, s = zamera
                K = red_dlzok(s, H, o)
                data_stranou_corr.append((bod, hz, round(s+K, 3)))
            zostavy_all[i]['stranou']['data'] = data_stranou_corr

    return zostavy_all


def write_body_stranou(file, zostavy):
    '''
    Do osobitneho suboru zapise spriemerovane uhly a dlzky pre body stranou
    '''
    with open(file, 'w', newline='') as obj:
        datwriter = csv.writer(obj, delimiter=' ',
                                quoting=csv.QUOTE_MINIMAL)
        datwriter.writerow(['Uhly pre body stranou'])
        datwriter.writerow(['uhol_name', 'Hz(g)', 'vzd(m)'])
        for zost in zostavy:
            bod_vzad = zost['bod_spat']['name']
            stanovisko = zost['stanovisko']['name']
            for zam_stran in zost['stranou']['data']:
                bod_stranou = zam_stran[0]
                Hz_stranou = zam_stran[1]
                vzd_stranou = zam_stran[2]
                angle_mark = '{}-{}-{}'.format(bod_vzad, stanovisko, bod_stranou)
                datwriter.writerow([angle_mark, Hz_stranou, vzd_stranou])


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


def check_namse_stranou(zostavy):
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


def compute_measurements(file, H, o, dist_reduce=True):
    '''
    file: str; zapisnik z merania (.txt)
    H: float; priblizna nadmorska vyska polygonoveho tahu.
    o: float; oprava pre 100m dlzky odcitana z diagramu dlzkovych oprav (mm)
    dist_reduce: bool; opravit dlzky o redukcie
    '''
    file_base = os.path.basename(file)
    # without extension
    file_name = os.path.splitext(file_base)[0]

    measures = get_measurements(file)
    measures = correct_first_stat(measures)
    check_names_bodvpred(measures)
    check_namse_stranou(measures)
    # Priemerovanie zamer z dvoch najspolahlivejsich skupin.
    zostavy_AVGed = []
    for zostava in measures:
        zostava_AVGed = adjust_zostava(zostava)
        zostavy_AVGed.append(zostava_AVGed)

    if dist_reduce:
        zostavy_AVGed = make_reductions(zostavy_AVGed, H, o)

    write_plx(file_name+'.plx', zostavy_AVGed)
    write_body_stranou(file_name+'_stranou.csv', zostavy_AVGed)



if __name__ == '__main__':
    compute_measurements(r'd:\Projects\POLYconverter\examples\example.txt', 500, -3)









