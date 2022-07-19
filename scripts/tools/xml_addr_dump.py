import fnmatch
import logging
import os
import struct
import xml.etree.ElementTree as Et

RAM_ADDR_OFFSET = 0x20000000
BLOCK_ADDR_INDEX = 0
BLOCK_SIZE_INDEX = 1


def block_print_string(block, size):
    value_unsigned = int.from_bytes(block, byteorder='little', signed=False)
    value_signed = int.from_bytes(block, byteorder='little', signed=True)
    if size == 4:
        value_float = struct.unpack('<f', bytes(block))[0]
    else:
        value_float = ''
    return ('{unsign:<10}   {unsign_hex:<10}    {sign:<11}  {sign_hex:<11}  {floatr:<11}'.
            format(unsign=str(value_unsigned),
                   unsign_hex=hex(value_unsigned),
                   sign=str(value_signed),
                   sign_hex=hex(value_signed),
                   floatr=value_float))


if __name__ == '__main__':
    try:
        ram_block = [0, 0]
        ram_blocks = [ram_block]

        os.chdir('output')
        # extract addresses and sizes of all RAM variables
        xml_tree = Et.parse('full_rom_dump.xml')
        for xml_elem in xml_tree.iter():
            if xml_elem.tag == 'DEFINED_DATA':
                block_addr = int(xml_elem.attrib['ADDRESS'], 16)
                if block_addr >= RAM_ADDR_OFFSET:
                    ram_block[BLOCK_ADDR_INDEX] = block_addr - RAM_ADDR_OFFSET
                    ram_block[BLOCK_SIZE_INDEX] = int(xml_elem.attrib['SIZE'], 16)
                    ram_blocks.append([*ram_block])

        # count number of ram_dump files
        ram_dump_count = 0
        input_files = []
        for file in os.listdir(os.getcwd()):
            if fnmatch.fnmatch(file, 'ram_dump_?.bin'):
                if file.endswith('{}.bin'.format(ram_dump_count + 1)):
                    ram_dump_count += 1
                    input_files.append(file)
                else:
                    break

        ram_blocks_values = [[[0, 0, 0, 0]
                              for j in range(ram_dump_count)]
                             for k in range(len(ram_blocks))]  # nested table of valid variables from all ram_dumps
        ram_blocks_common = [0 for i in range(len(ram_blocks))]  # number of ram_dumps with valid variable
        ram_dump_id = 0
        for input_file in input_files:  # iterate through all ram_dump files
            f = open(input_file, 'rb')
            ram_dump = list(f.read())
            block_index = 0
            for ram_block in ram_blocks:
                ram_dump_block = ram_dump[ram_block[BLOCK_ADDR_INDEX]:
                                          (ram_block[BLOCK_ADDR_INDEX] + ram_block[BLOCK_SIZE_INDEX])]
                value = 0
                for byte_elem in ram_dump_block:  # value at RAM address
                    value = (value << 8) | byte_elem
                if value != 0x00 and value != 0xFF and value != 0xFFFF and value != 0xFFFFFFFF:  # valid value
                    ram_blocks_values[block_index][ram_dump_id] = [*ram_dump_block]
                block_index += 1
            ram_dump_id += 1
            f.close()

        ram_blocks_common_count = 0
        values_string = '| ID     ADDR   SIZE |   '
        for i in range(ram_dump_count):
            values_string += '  UNSIGNED_DEC    UNSIGNED_HEX    SIGNED_DEC  UNSIGNED_HEX  FLOAT   |'
        print(values_string)
        for block_index in range(0, len(ram_blocks)):
            ram_blocks[block_index][BLOCK_ADDR_INDEX] += RAM_ADDR_OFFSET
            for ram_dump_id in range(ram_dump_count):
                if [0, 0, 0, 0] != ram_blocks_values[block_index][ram_dump_id]:
                    ram_blocks_common[block_index] += 1  # valid variable
            if ram_dump_count == ram_blocks_common[block_index]:  # all ram_dump files have a valid variable at address
                ram_blocks_common_count += 1
                values_string = ''
                for ram_dump_id in range(ram_dump_count):
                    values_string += block_print_string(ram_blocks_values[block_index][ram_dump_id],
                                                                ram_blocks[block_index][BLOCK_SIZE_INDEX]) + '  | '
                print('| {count:>3}   {addr}  {size}  |   {values}    '.format(count=ram_blocks_common_count,
                                                                     addr=hex(
                                                                         ram_blocks[block_index][BLOCK_ADDR_INDEX]),
                                                                     size=ram_blocks[block_index][BLOCK_SIZE_INDEX],
                                                                     values=values_string))
        print('OK!')
    except Exception as e:
        logging.exception('EXCEPTION')
        try:
            f.close()
        except NameError:
            pass
