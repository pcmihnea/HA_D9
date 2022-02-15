import fnmatch
import logging
import os

if __name__ == '__main__':
    try:
        file_index = 1

        os.chdir('output')
        f = open('full_rom_dump.bin', 'wb')
        for file in os.listdir(os.getcwd()):
            if fnmatch.fnmatch(file, 'rom_dump_?.bin') and file.endswith('{}.bin'.format(file_index)):
                file_index += 1
                f2 = open(file, 'rb')
                f.write(f2.read())
                f2.close()
                print('{}'.format(file))
        f.close()
        print('OK!')
    except Exception as e:
        logging.exception('EXCEPTION')
        try:
            f.close()
        except NameError:
            pass
        try:
            f2.close()
        except NameError:
            pass
