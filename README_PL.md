# BPMN

### Instalacja

- PyGraphViz: z tej strony (Windows): https://pygraphviz.github.io/documentation/stable/install.html#windows-install

Reszta
```
pip install numpy matplotlib pandas more-itertools
```

### Pliki:
 - `main.py` - wybierasz example do włączenia
 - `examples.py` - przykłady i ćwiczenia z labów - implementacje
 - `filters.py` - metody filtrujące
 - `network.py` - bazowa klasa dla procesu
 - `bpmn_network.py` - rozszerza powyzsze o rzeczy typu Causality itp, także implementacja alpha minera z jego przykladu
 - `drawing.py` - rysowanie z PyGraphViz
 - `network_factory.py` - tworzenie sieci z `direct_succession`, ale można dodać bezpośrednio z logów na przykład
 - `results/` - tu sie pojawiają wyrenderowane PNG diagramów
 
### Klasy
 
- `Node` - event lub brama (brama dziedziczy jako klasa `UtilityNode`)
- `Network` i `BPMNNetwork` - zarządza całą siecią. Ta druga rozszerza tą pierwszą
- `Edge` - reprezentuje krawędź, ale chyba to wywale bo póki co używam jedynie przy wyświetlaniu liczb, a poza tym to tylko przeszkadza i można łatwiej
 
### TODO

- Dopisać komentarze do reszty metod
- Dodać łączenie 2 bram tylko ładniej niż moja magia z notebooa **ALE**
- Może split i merge zrobić bardziej uniwersalnie - tzn nie szukać tak debilnie tylko owrapować w 1 metode gdzie podam 2 ścieżki (fragmenty sieci) które chce podzielić bramą
- Dodać obsługę macierzy przejść (jak tam kiedyś pokazywał) - może by to coś dało
