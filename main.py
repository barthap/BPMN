import examples
import matplotlib.pyplot as plt

if __name__ == '__main__':
    print('Hello!')

    # examples.lab1_repair_example()      # OK
    # examples.lab2_example()             # OK
    # examples.lab2_ex1()                 # OK
    examples.lab2_ex2()                 # OK
    for i in range (1, 10):
        examples.lab2_setA(i)
    # examples.lab2_setA(5)
    examples.loop1()
    examples.loop2()
    examples.loop3()

    """
    1 - OK
    2 - OK
    3 - dwie bramy obok siebie
    4 - podobno OK
    5 - OK
    6 - OK
    7 - totanla porazka
    8 - OK
    9 - OK
    """

    plt.show()
