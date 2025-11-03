from pathlib import Path

TLOBJECT_IN_TLS = [Path('scheme/lite_api.tl'), Path('scheme/ton_api.tl'), Path('scheme/tonlib_api.tl')]
IMPORT_DEPTH = 0
TLOBJECT_OUT = Path('tl_gen/')


def generate():
    from generator.parsers import parse_tl

    from generator.generators import generate_tlobjects
    print(TLOBJECT_IN_TLS)

    for file in TLOBJECT_IN_TLS:
        filename = file.name.split('.')[0]
        tlobjects = list(parse_tl(file))

        print('TLObjects...')
        generate_tlobjects(tlobjects, filename, IMPORT_DEPTH, TLOBJECT_OUT)

if __name__ == '__main__':
    generate()
