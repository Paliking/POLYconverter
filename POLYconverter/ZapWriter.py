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
