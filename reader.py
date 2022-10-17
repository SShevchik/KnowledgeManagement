import json


def main():
    f = open('result.json', 'rb')
    y = json.load(f)
    print(y)


if __name__ == '__main__':
    main()
