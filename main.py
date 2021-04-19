import examples
import matplotlib.pyplot as plt

if __name__ == '__main__':
    print('Hello!')

    examples.lab1_repair_example()      # OK
    # examples.lab2_example()             # OK
    # examples.lab2_ex1()                 # OK
    # examples.lab2_ex2()                 # !
    # for i in range (1, 5):             # OK: i=2
    #     examples.lab2_setA(i)
    # examples.lab2_setA(3)

    """
    1 - ~bramy na poczatku/koncu~ - JUZ OK
    2 - OK
    3 - 1 + dwie bramy obok siebie
    4 - tu jest jakas petla, nie wiem jak to ma byc
    5 - Prawie OK tylko nie wywalamy wszystkich parallel polaczen
    6 - krotka brama
    7 - totanla porazka
    8 - OK
    9 - to samo co 5
    """

    plt.show()
