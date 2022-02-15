import logging
import os
import shutil

RAM_SIZE = 0xBFFF
ROM_SIZE = 0x03FFFF

if __name__ == '__main__':
    try:
        ROM_START_ADDR = 0x8000000
        ROM_STOP_ADDR = ROM_START_ADDR + ROM_SIZE
        read_block_size = 1
        block_id = 0

        # maximum block_size, aligned to memory sizes
        block_size_limit = int(ROM_SIZE / (ROM_SIZE / (RAM_SIZE + 1)))
        for var in range(16):
            if (1 << var) <= block_size_limit:
                read_block_size = (1 << var)
            else:
                break

        file_path = os.path.join(os.getcwd(), 'output')
        if os.path.exists(file_path):
            shutil.rmtree(file_path)
        os.mkdir(file_path)
        os.chdir('output')
        f = open('jlink_cmd_gen.txt', 'w')
        f.write('Write4 E000EDF0, A05F0000\n'
                'Sleep 10\n'
                'ClrRESET\n'
                'Sleep 200\n'
                'SetRESET\n'
                'Sleep 10\n'
                'Write4 e000ed08, f0000000\n'
                'Write4 e000ed04, 80000000\n'
                'Write4 40021014, 00000015\n')
        for block_start_addr in range(ROM_START_ADDR, ROM_STOP_ADDR, read_block_size):
            block_id += 1
            f.write('Write4 40020008, 00004AC0\n'
                    'Write4 4002000c, {block_size:08X}\n'
                    'Write4 40020010, {block_start_addr:08X}\n'
                    'Write4 40020014, 20000000\n'
                    'Write4 40020008, 00004AC1\n'
                    'Sleep 200\n'
                    'SaveBin {file_path}\\rom_dump_{block_id}.bin, 20000000, {block_size:X}\n'.format(
                block_size=read_block_size,
                block_start_addr=block_start_addr, file_path=file_path, block_id=block_id))
            print('{block_id}. {start:#08x}:{end:#08x}'.format(block_id=block_id, start=block_start_addr,
                                                               end=(block_start_addr + read_block_size - 1)))
        f.close()
        print('OK!')
    except Exception as e:
        logging.exception('EXCEPTION')
        try:
            f.close()
        except NameError:
            pass
