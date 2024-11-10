import typing, random

UPPERCASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
LOWERCASE = 'abcdefghijklmnopqrstuvwxyz'
NUMBERS = '0123456789'

def gen_random_id(length: int = 10):
    return ''.join(random.choice(UPPERCASE + LOWERCASE + NUMBERS) for _ in range(length))

def sliding_win(iterable: typing.Iterable, n: int = 3):
    for i in range(len(iterable)-n+1):
        yield [iterable[j] for j in range(i, i+n)]