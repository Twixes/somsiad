# Copyright 2018-2021 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from plugins.trade_sundays import determine_nearest_trade_sunday_after_date
from utilities import join_using_and
from discord.ext import commands, tasks
import datetime as dt
from configuration import configuration
from core import Help as _Help
from core import cooldown
import discord
import hashlib
from somsiad import Somsiad

COTD_TIME = (12, 00)

NAME_DAYS = {
    1: {
        1: ['Mieszka', 'Mieczysława', 'Marii'],
        2: ['Izydora', 'Bazylego', 'Grzegorza'],
        3: ['Arlety', 'Genowefy', 'Danuty'],
        4: ['Tytusa', 'Anieli', 'Eugeniusza'],
        5: ['Hanny', 'Szymona', 'Edwarda'],
        6: ['Kacpra', 'Melchiora', 'Baltazara'],
        7: ['Juliana', 'Lucjana', 'Rajmunda'],
        8: ['Seweryna', 'Mścisława', 'Juliusza'],
        9: ['Marceliny', 'Marianny', 'Juliana'],
        10: ['Wilhelma', 'Dobrosława', 'Danuty'],
        11: ['Honoraty', 'Teodozjusza', 'Matyldy'],
        12: ['Grety', 'Arkadiusza', 'Rajmunda'],
        13: ['Bogumiły', 'Weroniki', 'Hilarego'],
        14: ['Feliksa', 'Domosława', 'Niny'],
        15: ['Pawła', 'Arnolda', 'Izydora'],
        16: ['Marcelego', 'Włodzimierza', 'Waldemara'],
        17: ['Antoniego', 'Rościsława', 'Jana'],
        18: ['Piotra', 'Małgorzaty'],
        19: ['Henryka', 'Mariusza', 'Marty'],
        20: ['Fabiana', 'Sebastiana'],
        21: ['Agnieszki', 'Jarosława'],
        22: ['Anastazego', 'Wincentego'],
        23: ['Ildefonsa', 'Rajmunda'],
        24: ['Felicji', 'Franciszka', 'Rafała'],
        25: ['Pawła', 'Miłosza', 'Elwiry'],
        26: ['Tymoteusza', 'Michała', 'Tytusa'],
        27: ['Przybysława', 'Anieli', 'Jerzego'],
        28: ['Walerego', 'Radomira', 'Tomasza'],
        29: ['Zdzisława', 'Franciszka', 'Józefa'],
        30: ['Macieja', 'Martyny', 'Teofila'],
        31: ['Marceli', 'Ludwiki', 'Jana'],
    },
    2: {
        1: ['Brygidy', 'Ignacego', 'Seweryna'],
        2: ['Marii', 'Miłosława'],
        3: ['Błażeja', 'Oskara'],
        4: ['Andrzeja', 'Weroniki', 'Joanny'],
        5: ['Agaty', 'Adelajdy', 'Izydora'],
        6: ['Doroty', 'Bogdana', 'Pawła'],
        7: ['Ryszarda', 'Teodora', 'Romana'],
        8: ['Hieronima', 'Sebastiana', 'Ireny'],
        9: ['Apolonii', 'Eryki', 'Cyryla'],
        10: ['Elwiry', 'Jacka', 'Scholastyki'],
        11: ['Lucjana', 'Olgierda', 'Grzegorza'],
        12: ['Eulalii', 'Radosława', 'Modesta'],
        13: ['Grzegorza', 'Katarzyny'],
        14: ['Cyryla', 'Metodego', 'Walentego'],
        15: ['Jowity', 'Faustyna', 'Zygfryda'],
        16: ['Danuty', 'Julianny', 'Daniela'],
        17: ['Aleksego', 'Zbigniewa', 'Łukasza'],
        18: ['Szymona', 'Konstancji', 'Flawiana'],
        19: ['Arnolda', 'Konrada', 'Marcelego'],
        20: ['Leona', 'Ludomira', 'Zenobiusza'],
        21: ['Eleonory', 'Fortunata', 'Roberta'],
        22: ['Marty', 'Małgorzaty', 'Piotra'],
        23: ['Romany', 'Damiana', 'Polikarpa'],
        24: ['Macieja', 'Bogusza', 'Sergiusza'],
        25: ['Wiktora', 'Cezarego'],
        26: ['Mirosława', 'Aleksandra'],
        27: ['Gabriela', 'Anastazji'],
        28: ['Romana', 'Ludomira', 'Lecha'],
    },
    3: {
        1: ['Antoniny', 'Radosława', 'Dawida'],
        2: ['Heleny', 'Halszki', 'Pawła'],
        3: ['Maryny', 'Kunegundy', 'Tycjana'],
        4: ['Łucji', 'Kazimierza', 'Eugeniusza'],
        5: ['Adriana', 'Fryderyka', 'Teofila'],
        6: ['Róży', 'Jordana', 'Agnieszki'],
        7: ['Tomasza', 'Perpetuy', 'Felicyty'],
        8: ['Beaty', 'Wincentego', 'Jana'],
        9: ['Franciszki', 'Brunona'],
        10: ['Cypriana', 'Marcela', 'Aleksandra'],
        11: ['Ludosława', 'Konstantyna', 'Benedykta'],
        12: ['Grzegorza', 'Justyna', 'Alojzego'],
        13: ['Bożeny', 'Krystyny'],
        14: ['Leona', 'Matyldy', 'Łazarza'],
        15: ['Longina', 'Klemensa', 'Ludwiki'],
        16: ['Izabeli', 'Oktawii', 'Hilarego'],
        17: ['Patryka', 'Zbigniewa', 'Gertrudy'],
        18: ['Cyryla', 'Edwarda', 'Boguchwały'],
        19: ['Józefa', 'Bogdana'],
        20: ['Klaudii', 'Eufemii', 'Maurycego'],
        21: ['Lubomira', 'Benedykta'],
        22: ['Katarzyny', 'Bogusława'],
        23: ['Pelagii', 'Oktawiana', 'Feliksa'],
        24: ['Marka', 'Gabriela', 'Katarzyny'],
        25: ['Marioli', 'Wieäczysława', 'Ireneusza'],
        26: ['Larysy', 'Emanyela', 'Teodora'],
        27: ['Lidii', 'Ernesta'],
        28: ['Anieli', 'Sykstusa', 'Jana'],
        29: ['Wiktoryna', 'Helmuta', 'Eustachego'],
        30: ['Anieli', 'Kwiryna', 'Leonarda'],
        31: ['Beniamina', 'Dobromierza', 'Leonarda'],
    },
    4: {
        1: ['Teodory', 'Grażyny', 'Ireny'],
        2: ['Władysława', 'Franciszka', 'Teodozji'],
        3: ['Ryszarda', 'Pankracego', 'Ingi'],
        4: ['Izydora', 'Wacława'],
        5: ['Ireny', 'Wincentego'],
        6: ['Izoldy', 'Celestyna', 'Wilhelma'],
        7: ['Rufina', 'Celestyna', 'Jana'],
        8: ['Cezaryny', 'Dionizego', 'Julii'],
        9: ['Marii', 'Dymitra', 'Heliodora'],
        10: ['Michała', 'Makarego'],
        11: ['Filipa', 'Leona'],
        12: ['Juliusza', 'Lubosława', 'Zenona'],
        13: ['Przemysława', 'Hermenegildy', 'Marcina'],
        14: ['Bereniki', 'Waleriana', 'Justyny'],
        15: ['Ludwiny', 'Wacławy', 'Anastazji'],
        16: ['Kseni', 'Cecylii', 'Bernardety'],
        17: ['Rudolfa', 'Roberta'],
        18: ['Bogusławy', 'Apoloniusza'],
        19: ['Adolfa', 'Tymona', 'Leona'],
        20: ['Czesława', 'Agnieszki', 'Mariana'],
        21: ['Anzelma', 'Bartosza', 'Feliksa'],
        22: ['Kai', 'Leonii', 'Sotera'],
        23: ['Jerzego', 'Wojciecha'],
        24: ['Horacego', 'Feliksa', 'Grzegorza'],
        25: ['Marka', 'Jarosława'],
        26: ['Marzeny', 'Klaudiusza', 'Marii'],
        27: ['Zyty', 'Teofila', 'Felicji'],
        28: ['Piotra', 'Walerii', 'Witalisa'],
        29: ['Rity', 'Katarzyny', 'Bogusława'],
        30: ['Mariana', 'Donaty', 'Tamary'],
    },
    5: {
        1: ['Józefa', 'Jeremiasza', 'Filipa'],
        2: ['Zygmunta', 'Atanazego', 'Anatola'],
        3: ['Marii', 'Antoniny'],
        4: ['Moniki', 'Floriana', 'Władysława'],
        5: ['Ireny', 'Waldemara'],
        6: ['Judyty', 'Jakuba', 'Filipa'],
        7: ['Gizeli', 'Ludmiły', 'Benedykta'],
        8: ['Stanisława', 'Lizy', 'Wiktora'],
        9: ['Bożydara', 'Grzegorza', 'Karoliny'],
        10: ['Izydora', 'Antoniny', 'Symeona'],
        11: ['Igi', 'Miry', 'Władysławy'],
        12: ['Pankracego', 'Dominika', 'Achillesa'],
        13: ['Serwacego', 'Roberta', 'Glorii'],
        14: ['Bonifacego', 'Dobiesława', 'Macieja'],
        15: ['Zofii', 'Nadziei', 'Izydora'],
        16: ['Andrzeja', 'Jędrzeja', 'Szymona'],
        17: ['Paschalisa', 'Sławomira', 'Weroniki'],
        18: ['Eryka', 'Feliksa', 'Jana'],
        19: ['Iwa', 'Piotra', 'Celestyna'],
        20: ['Bazylego', 'Bernardyna', 'Aleksandra'],
        21: ['Wiktora', 'Kryspina', 'Tymoteusza'],
        22: ['Heleny', 'Wiesławy', 'Ryty'],
        23: ['Iwony', 'Dezyderego', 'Kryspina'],
        24: ['Joanny', 'Zuzanny'],
        25: ['Grzegorza', 'Urbana', 'Magdaleny'],
        26: ['Filipa', 'Pauliny'],
        27: ['Augustyna', 'Juliana', 'Magdaleny'],
        28: ['Jaromira', 'Justa', 'Justyny'],
        29: ['Magdaleny', 'Bogumiły', 'Urszuli'],
        30: ['Ferdynanda', 'Karola', 'Jana'],
        31: ['Anieli', 'Petroneli'],
    },
    6: {
        1: ['Justyna', 'Anieli', 'Konrada'],
        2: ['Marianny', 'Marcelina', 'Piotra'],
        3: ['Leszka', 'Tamary', 'Karola'],
        4: ['Kwiryny', 'Franciszka'],
        5: ['Waltera', 'Bonifacego', 'Walerii'],
        6: ['Norberta', 'Laurentego', 'Bogumiła'],
        7: ['Roberta', 'Wiesława'],
        8: ['Medarda', 'Maksyma', 'Seweryna'],
        9: ['Pelagii', 'Dominika', 'Efrema'],
        10: ['Bogumiła', 'Małgorzaty', 'Diany'],
        11: ['Barnaby', 'Radomiła', 'Feliksa'],
        12: ['Janiny', 'Onufrego', 'Leona'],
        13: ['Lucjana', 'Antoniego'],
        14: ['Bazylego', 'Elwiry', 'Michała'],
        15: ['Wita', 'Jolanty'],
        16: ['Aliny', 'Benona', 'Anety'],
        17: ['Laury', 'Marcjana', 'Alberta'],
        18: ['Marka', 'Elżbiety'],
        19: ['Gerwazego', 'Protazego'],
        20: ['Diny', 'Bogny', 'Florentyny'],
        21: ['Alicji', 'Alojzego'],
        22: ['Pauliny', 'Tomasza', 'Jana'],
        23: ['Wandy', 'Zenona'],
        24: ['Jana', 'Danuty'],
        25: ['Łucji', 'Wilhelma', 'Doroty'],
        26: ['Jana', 'Pawła'],
        27: ['Maryli', 'Władysława', 'Cyryla'],
        28: ['Leona', 'Ireneusza'],
        29: ['Piotra', 'Pawła'],
        30: ['Emilii', 'Lucyny'],
    },
    7: {
        1: ['Haliny', 'Mariana', 'Marcina'],
        2: ['Jagody', 'Urbama', 'Marii'],
        3: ['Jacka', 'Anatola', 'Tomasza'],
        4: ['Odona', 'Malwiny', 'Elżbiety'],
        5: ['Marii', 'Antoniego'],
        6: ['Gotarda', 'Dominiki', 'Łucji'],
        7: ['Cyryla', 'Estery', 'Metodego'],
        8: ['Edgara', 'Elżbiety', 'Eugeniusza'],
        9: ['Lukrecji', 'Weroniki', 'Zenona'],
        10: ['Sylwany', 'Witalisa', 'Antoniego'],
        11: ['Olgi', 'Kaliny', 'Benedykta'],
        12: ['Jana', 'Brunona', 'Bonifacego'],
        13: ['Henryka', 'Kingi', 'Andrzeja'],
        14: ['Ulryka', 'Bonawentury', 'Kamila'],
        15: ['Henryka', 'Włodzimierza', 'Dawida'],
        16: ['Mariki', 'Benity', 'Eustachego'],
        17: ['Anety', 'Bogdana', 'Jadwigi'],
        18: ['Erwina', 'Kamila', 'Szymona'],
        19: ['Wincentego', 'Wodzisława', 'Marcina'],
        20: ['Czesława', 'Hieronioma', 'Małgorzaty'],
        21: ['Daniela', 'Dalidy', 'Wawrzyńca'],
        22: ['Marii', 'Magdaleny'],
        23: ['Stwosza', 'Bogny', 'Brygidy'],
        24: ['Kingi', 'Krystyny'],
        25: ['Walentyny', 'Krzysztofa', 'Jakuba'],
        26: ['Anny', 'Mirosławy', 'Grażyny'],
        27: ['Lilii', 'Julii', 'Natalii'],
        28: ['Aidy', 'Marceli', 'Wiktora'],
        29: ['Olafa', 'Marty', 'Ludmiły'],
        30: ['Julity', 'Piotra', 'Aldony'],
        31: ['Ignacego', 'Lubomira', 'Heleny'],
    },
    8: {
        1: ['Nadii', 'Justyna', 'Juliana'],
        2: ['Kariny', 'Gustawa', 'Euzebiusza'],
        3: ['Lidii', 'Augusta', 'Nikodema'],
        4: ['Dominika', 'Protazego', 'Jana'],
        5: ['Oswalda', 'Marii', 'Mariana'],
        6: ['Sławy', 'Jakuba', 'Oktawiana'],
        7: ['Kajetana', 'Doroty', 'Sykstusa'],
        8: ['Cypriana', 'Emiliana', 'Dominika'],
        9: ['Romana', 'Ryszarda', 'Edyty'],
        10: ['Borysa', 'Filomeny', 'Wawrzyńca'],
        11: ['Klary', 'Zuzanny', 'Lecha'],
        12: ['Innocentego', 'Lecha', 'Euzebii'],
        13: ['Diany', 'Hipolita', 'Poncjana'],
        14: ['Alfreda', 'Euzebiusza', 'Maksymiliana'],
        15: ['Napoleona', 'Stelii'],
        16: ['Rocha', 'Stefana', 'Joachima'],
        17: ['Żanny', 'Mirona', 'Jacka'],
        18: ['Ilony', 'Bronisława', 'Heleny'],
        19: ['Bolesława', 'Juliana'],
        20: ['Bernarda', 'Samuela', 'Sobiesława'],
        21: ['Joanny', 'Kazimiery', 'Piusa'],
        22: ['Cezarego', 'Tymoteusza'],
        23: ['Apolinarego', 'Filipa'],
        24: ['Jerzego', 'Bartosza', 'Haliny'],
        25: ['Luizy', 'Ludwika', 'Józefa'],
        26: ['Marii', 'Aleksandra'],
        27: ['Józefa', 'Kolasantego'],
        28: ['Patrycji', 'Wyszomira', 'Augustyna'],
        29: ['Jana', 'Sabiny', 'Racibora'],
        30: ['Róży', 'Szczęsnego', 'Feliksa'],
        31: ['Ramony', 'Rajmunda', 'Bogdana'],
    },
    9: {
        1: ['Idziego', 'Bronisława'],
        2: ['Stefana', 'Wilhelma', 'Juliana'],
        3: ['Izabeli', 'Szymona', 'Grzegorza'],
        4: ['Rozalii', 'Róży'],
        5: ['Doroty', 'Wawrzyńca', 'Teodora'],
        6: ['Beaty', 'Eugeniusza'],
        7: ['Reginy', 'Melchiora', 'Domosławy'],
        8: ['Marii', 'Adrianny', 'Serafiny'],
        9: ['Ścibora', 'Sergiusza', 'Piotra'],
        10: ['Łukasza', 'Aldony', 'Mścisława'],
        11: ['Jacka', 'Prota', 'Dagny', 'Hiacynta'],
        12: ['Gwidona', 'Radzimira', 'Marii'],
        13: ['Eugenii', 'Aureliusza', 'Jana'],
        14: ['Roksany', 'Bernarda', 'Cypriana'],
        15: ['Albina', 'Nikodema', 'Marii'],
        16: ['Edyty', 'Korneliusza', 'Cypriana'],
        17: ['Franciszka', 'Roberta', 'Justyna'],
        18: ['Irmy', 'Stanisława', 'Ireny'],
        19: ['Januarego', 'Konstancji', 'Teodora'],
        20: ['Filipiny', 'Eustachego', 'Euzebii'],
        21: ['Jonasza', 'Mateusza', 'Hipolita'],
        22: ['Tomasza', 'Maurycego', 'Joachima'],
        23: ['Tekli', 'Bogusława', 'Linusa'],
        24: ['Gerarda', 'Ruperta', 'Tomiry'],
        25: ['Aurelii', 'Władysława', 'Kleofasa'],
        26: ['Wawrzyńca', 'Kosmy', 'Damiana'],
        27: ['Wincentego', 'Mirabeli', 'Justyny'],
        28: ['Wacława', 'Tymona', 'Marka'],
        29: ['Michała', 'Gabriela', 'Rafała'],
        30: ['Wery', 'Honoriusza', 'Hieronima'],
    },
    10: {
        1: ['Danuty', 'Remigiusza', 'Teresy'],
        2: ['Teofila', 'Dionizego', 'Sławomira'],
        3: ['Teresy', 'Heliodora', 'Jana'],
        4: ['Rozalii', 'Edwina', 'Franciszka'],
        5: ['Placyda', 'Apolinarego'],
        6: ['Artura', 'Brunona'],
        7: ['Marii', 'Marka', 'Mirelli'],
        8: ['Pelagii', 'Brygidy', 'Walerii'],
        9: ['Amolda', 'Dionizego', 'Wincentego'],
        10: ['Pauliny', 'Danieli', 'Leona'],
        11: ['Aldony', 'Aleksandra', 'Dobromiry'],
        12: ['Eustachego', 'Maksymiliana', 'Edwina'],
        13: ['Geralda', 'Edwarda', 'Honorata'],
        14: ['Liwii', 'Kaliksta', 'Bernarda'],
        15: ['Jadwigi', 'Teresy', 'Florentyny'],
        16: ['Gawła', 'Ambrożego'],
        17: ['Wiktora', 'Marity', 'Ignacego'],
        18: ['Juliana', 'Łukasza'],
        19: ['Ziemowita', 'Jana', 'Pawła'],
        20: ['Ireny', 'Kleopatry', 'Jana'],
        21: ['Urszuli', 'Hilarego', 'Jakuba'],
        22: ['Halki', 'Filipa', 'Salomei'],
        23: ['Marleny', 'Seweryna', 'Igi'],
        24: ['Rafała', 'Marcina', 'Antoniego'],
        25: ['Darii', 'Wilhelminy', 'Bonifacego'],
        26: ['Lucjana', 'Ewarysta', 'Damiana'],
        27: ['Iwony', 'Sabiny'],
        28: ['Szymona', 'Tadeusza'],
        29: ['Euzebii', 'Wioletty', 'Felicjana'],
        30: ['Zenobii', 'Przemysława', 'Edmunda'],
        31: ['Urbana', 'Saturnina', 'Krzysztofa'],
    },
    11: {
        1: ['Wszystkich Świętych'],
        2: ['Bohdany', 'Bożydara'],
        3: ['Sylwii', 'Marcina', 'Huberta'],
        4: ['Karola', 'Olgierda'],
        5: ['Elżbiety', 'Sławomira', 'Dominika'],
        6: ['Feliksa', 'Leonarda', 'Ziemowita'],
        7: ['Antoniego', 'Żytomira', 'Ernesta'],
        8: ['Seweryna', 'Bogdana', 'Klaudiusza'],
        9: ['Aleksandra', 'Ludwika', 'Teodora'],
        10: ['Leny', 'Ludomira', 'Leona'],
        11: ['Marcina', 'Batłomieja', 'Teodora'],
        12: ['Renaty', 'Witolda', 'Jozafata'],
        13: ['Mateusza', 'Izaaka', 'Stanisława'],
        14: ['Rogera', 'Serafina', 'Wawrzyäca'],
        15: ['Alberta', 'Leopolda'],
        16: ['Gertrudy', 'Edmunda', 'Marii'],
        17: ['Salomei', 'Grzegorza', 'Elżbiety'],
        18: ['Romana', 'Klaudyny', 'Karoliny'],
        19: ['Seweryny', 'Maksyma', 'Salomei'],
        20: ['Anatola', 'Sędzimira', 'Rafała'],
        21: ['Janusza'],
        22: ['Cecylii', 'Wszemiły', 'Stefana'],
        23: ['Adelii', 'Klemensa', 'Felicyty'],
        24: ['Flory', 'Emmy', 'Chryzogona'],
        25: ['Erazma', 'Katarzyny'],
        26: ['Delfiny', 'Sylwestra', 'Konrada'],
        27: ['Waleriana', 'Wirgiliusza', 'Maksyma'],
        28: ['Lesława', 'Zdzisława', 'Stefana'],
        29: ['Błażeja', 'Saturnina'],
        30: ['Andrzeja', 'Maury', 'Konstantego'],
    },
    12: {
        1: ['Natalii', 'Eligiusza', 'Edmunda'],
        2: ['Balbiny', 'Bibianny', 'Pauliny'],
        3: ['Franciszka', 'Ksawerego', 'Kasjana'],
        4: ['Barbary', 'Krystiana', 'Jana'],
        5: ['Sabiny', 'Krystyny', 'Edyty'],
        6: ['Mikołaja', 'Jaremy', 'Emiliana'],
        7: ['Marcina', 'Ambrożego', 'Teodora'],
        8: ['Marii', 'Światozara', 'Makarego'],
        9: ['Wiesława', 'Leokadii', 'Joanny'],
        10: ['Julii', 'Danieli', 'Bogdana'],
        11: ['Damazego', 'Waldemara', 'Daniela'],
        12: ['Dagmary', 'Aleksandra', 'Ady'],
        13: ['Łucji', 'Otylii'],
        14: ['Alfreda', 'Izydora', 'Jana'],
        15: ['Niny', 'Celiny', 'Waleriana'],
        16: ['Albiny', 'Zdzisławy', 'Alicji'],
        17: ['Olimpii', 'Łazarza', 'Floriana'],
        18: ['Gracjana', 'Bogusława', 'Laurencji'],
        19: ['Gabrieli', 'Dariusza', 'Eleonory'],
        20: ['Bogumiły', 'Dominika'],
        21: ['Tomisława', 'Seweryna', 'Piotra'],
        22: ['Zenona', 'Honoraty', 'Franciszki'],
        23: ['Wiktorii', 'Sławomiry', 'Jana'],
        24: ['Adama', 'Ewy', 'Eweliny'],
        25: ['Anastazji', 'Eugenii'],
        26: ['Dionizego', 'Szczepana'],
        27: ['Jana', 'Żanety', 'Maksyma'],
        28: ['Teofilii', 'Godzisława', 'Cezarego'],
        29: ['Dawida', 'Tomasza', 'Dominika'],
        30: ['Rainera', 'Eugeniusza', 'Irmy'],
        31: ['Sylwestra', 'Melanii', 'Mariusza'],
    },
}


class Help(commands.Cog):
    COMMANDS = (
        _Help.Command(('pomocy', 'pomoc', 'help'), (), 'Wysyła ci wiadomość pomocy z objaśnieniem komend.', '❓'),
        _Help.Command(('8-ball', '8ball', 'eightball', '8', 'czy'), 'pytanie', 'Zadaje <pytanie> magicznej kuli.', '🎱'),
        _Help.Command(
            ('wybierz',),
            ('opcje',),
            'Wybiera jedną z oddzielonych przecinkami, średnikami, "lub", "albo" bądź "czy" <opcji>.',
            '👉',
            ['wybierz 420, 69, 666', 'wybierz pies czy kot'],
        ),
        _Help.Command(('rzuć', 'rzuc'), ('?liczba kości', '?liczba ścianek kości'), 'Rzuca kością/koścmi.', '🎲'),
        _Help.Command(
            ('google', 'gugiel', 'g'),
            'zapytanie',
            'Wysyła <zapytanie> do [Google](https://www.google.com) i zwraca najlepiej pasującą stronę.',
            '🇬',
        ),
        _Help.Command(
            ('googleimage', 'gi', 'i'),
            'zapytanie',
            'Wysyła <zapytanie> do [Google](https://www.google.pl/imghp) i zwraca najlepiej pasujący obrazek.',
            '🖼',
        ),
        _Help.Command(
            ('youtube', 'yt', 'tuba'),
            'zapytanie',
            'Zwraca z [YouTube](https://www.youtube.com) najlepiej pasujące do <zapytania> wideo.',
            '▶️',
        ),
        _Help.Command(
            ('wikipedia', 'wiki', 'w'),
            ('dwuliterowy kod języka', 'hasło'),
            'Sprawdza znaczenie <hasła> w danej wersji językowej [Wikipedii](https://www.wikipedia.org/).',
            '📖',
        ),
        _Help.Command(
            'tmdb',
            'zapytanie/podkomenda',
            'Zwraca z [TMDb](https://www.themoviedb.org/) najlepiej pasujący do <?zapytania> film/serial/osobę. '
            'Użyj bez <?zapytania/podkomendy>, by dowiedzieć się więcej.',
            '🎬',
        ),
        _Help.Command(
            'spotify',
            '?użytkownik Discorda',
            'Zwraca informacje na temat utworu obecnie słuchanego przez <?użytkownika Discorda> na Spotify. '
            'Jeśli nie podano <?użytkownika Discorda>, przyjmuje ciebie.',
            '🎶',
        ),
        _Help.Command(
            ('lastfm', 'last', 'fm', 'lfm'),
            'użytkownik Last.fm',
            'Zwraca z Last.fm informacje na temat utworu obecnie słuchanego przez <użytkownika Last.fm>.',
            '🎧',
        ),
        _Help.Command(
            ('goodreads', 'gr', 'książka', 'ksiazka'),
            'tytuł/autor',
            'Zwraca z [goodreads](https://www.goodreads.com) informacje na temat książki najlepiej pasującej do '
            '<tytułu/autora>.',
            '📚',
        ),
        _Help.Command(
            ('urbandictionary', 'urban'),
            'wyrażenie',
            'Sprawdza znaczenie <wyrażenia> w [Urban Dictionary](https://www.urbandictionary.com).',
            '📔',
        ),
        _Help.Command(
            ('wolframalpha', 'wolfram', 'wa', 'kalkulator', 'oblicz', 'policz', 'przelicz', 'konwertuj'),
            ('zapytanie',),
            '[Wolfram Alpha](https://www.wolframalpha.com/) – oblicza, przelicza, podaje najróżniejsze informacje. '
            'Usługa po angielsku.',
            '🧠',
        ),
        _Help.Command(('isitup', 'isup', 'czydziała', 'czydziala'), 'link', 'Sprawdza status danej strony.', '🚦'),
        _Help.Command(
            ('rokszkolny', 'wakacje', 'ilejeszcze'),
            '?podkomenda',
            'Zwraca ile jeszcze zostało do końca roku szkolnego lub wakacji. '
            'Użyj z <podkomendą> "matura", by dowiedzieć się ile zostało do matury.',
            '🎓',
        ),
        _Help.Command(('subreddit', 'sub', 'r'), 'subreddit', 'Zwraca informacje o <subreddicie>.', '🛸'),
        _Help.Command(('user', 'u'), 'użytkownik Reddita', 'Zwraca informacje o <użytkowniku Reddita>.', '👽'),
        _Help.Command(
            ('disco', 'd'),
            '?podkomenda',
            'Komendy związane z odtwarzaniem muzyki na kanałach głosowych. Użyj bez <?podkomendy>, by dowiedzieć się więcej.',
            '📻',
        ),
        _Help.Command('role', (), 'Wyświetla wszystkie role na serwerze wraz z liczbą członków je mających.', '🔰'),
        _Help.Command(
            ('stat', 'staty', 'aktywnosć', 'aktywnosc'),
            '?użytkownik/kanał/kategoria/podkomenda',
            'Komendy związane z raportami serwerowych statystyk. '
            'Użyj bez <?użytkownika/kanału/kategorii/podkomendy>, by dowiedzieć się więcej.',
            '📈',
        ),
        _Help.Command(
            'urodziny',
            '?podkomenda/użytkownik',
            'Komendy związane z datami urodzin. Użyj bez <?podkomendy/użytkownika>, by dowiedzieć się więcej.',
            '🎂',
        ),
        _Help.Command(
            ('handlowe', 'niedzielehandlowe'),
            '?podkomenda',
            'Kiedy wypada niedziela handlowa? Czy zrobisz dziś zakupy? W jakich datach Polska jest zamknięta? Sprawdź, kiedy sklepy będą otwarte [KALENDARZ]',
            '🛒',
        ),
        _Help.Command(
            ('przypomnij', 'przypomnienie', 'pomidor'),
            ('liczba minut/data i godzina, bez spacji', 'treść'),
            'Przypomina o <treści> po upływie podanego czasu.',
            '🍅',
            ['przypomnij 21.08.2022T12:00 Wyłączyć piekarnik!', 'przypomnij 12d3h5m Przeczytać książkę'],
        ),
        _Help.Command(
            ('spal', 'burn'),
            ('liczba minut/data i godzina, bez spacji', '?treść (może to być załącznik)'),
            'Usuwa wiadomość po upływie podanego czasu.',
            '🔥',
            ['spal 2h Nudesy'],
            non_ai_usable=True
        ),
        _Help.Command(
            ('kolory', 'kolor', 'kolorki', 'kolorek'),
            '?podkomenda',
            'Komendy związane z kolorami nicków samodzielnie wybieranymi przez użytkowników. '
            'Użyj bez <?podkomendy>, by dowiedzieć się więcej.',
            '🎨',
        ),
        _Help.Command(
            'przypinki',
            '?podkomenda',
            'Komendy związane z archiwizacją przypiętych wiadomości. '
            'Użyj bez <?podkomendy>, by dowiedzieć się więcej.',
            '📌',
            non_ai_usable=True
        ),
        _Help.Command(
            ('głosowanie', 'glosowanie', 'ankieta'),
            ('?liczba minut/data i godzina, bez spacji', 'sprawa'),
            'Gdy <sprawa> jest w formacie "A. Opcja pierwsza, B. Opcja druga, ...", rozpoczyna głosowanie nad najpopularniejszą z opcji.\n'
            'Gdy <sprawa> jest w formacie "1. Opcja pierwsza, 2. Opcja druga, ..., n. Opcja n-ta", rozpoczyna głosowanie nad uśrednioną wartość odpowiedzi w skali od 1 do n .\n'
            'Jeśli <sprawa> nie jest w żadnym z powyższych formatów, rozpoczyna głosowanie "za/przeciw".\n'
            'Ogłasza wynik po upływie podanego czasu, jeśli go podano.',
            '🗳',
        ),
        _Help.Command(
            ('pomógł', 'pomogl'), '?użytkownik Discorda', 'Oznacza pomocną wiadomość za pomocą reakcji.', '😺',
            non_ai_usable=True
        ),
        _Help.Command(
            ('niepomógł', 'niepomogl'), '?użytkownik Discorda', 'Oznacza niepomocną wiadomość za pomocą reakcji.', '😾',
            non_ai_usable=True
        ),
        _Help.Command(
            ('hm', 'hmm', 'hmmm', 'hmmmm', 'hmmmmm', 'myśl', 'mysl', 'think', 'thinking', '🤔'),
            '?użytkownik Discorda',
            '🤔',
            '🤔',
            non_ai_usable=True
        ),
        _Help.Command(('^', 'to', 'this', 'up', 'upvote'), '?użytkownik Discorda', '⬆', '⬆',
            non_ai_usable=True),
        _Help.Command('f', '?użytkownik Discorda', 'F', '🇫',
            non_ai_usable=True ),
        _Help.Command(
            ('zareaguj', 'reaguj', 'x'),
            ('?użytkownik Discorda', 'reakcje'),
            'Dodaje <reakcje> do ostatniej wiadomości wysłanej na kanale '
            '(jeśli podano <?użytkownika Discorda>, to ostatnią jego autorstwa na kanale).',
            '💬',
        ),
        _Help.Command('oof', (), 'Oof!', '😤',
            non_ai_usable=True),
        _Help.Command(
            'oof ile',
            '?użytkownik Discorda',
            'Zlicza oofnięcia dla <?użytkownika Discorda> lub, jeśli nie podano <?użytkownika Discorda>, dla ciebie.',
            '😱',
            non_ai_usable=True
        ),
        _Help.Command('oof serwer', (), 'Zlicza oofnięcia na serwerze i generuje ranking ooferów.', '🤠',
            non_ai_usable=True),
        _Help.Command(
            ('obróć', 'obroc', 'niewytrzymie'),
            ('?użytkownik', '?stopni/razy'),
            'Obraca ostatni załączony na kanale lub, jeśli podano <?użytkownika>, na kanale przez <?użytkownika> obrazek <?stopni/razy> (domyślnie 90 stopni/1 raz) zgodnie z ruchem wskazówek zegara.',
            '🔁',
        ),
        _Help.Command(
            ('deepfry', 'usmaż', 'głębokosmaż', 'usmaz', 'glebokosmaz'),
            ('?użytkownik', '?poziom usmażenia'),
            'Smaży ostatni załączony na kanale lub, jeśli podano <?użytkownika>, na kanale przez <?użytkownika> obrazek <?poziom usmażenia> razy (domyślnie 2 razy).',
            '🍟',
        ),
        _Help.Command(
            ('było', 'bylo', 'byo', 'robot9000', 'r9k'),
            '?użytkownik',
            'Sprawdza czy ostatnio załączony na kanale lub, jeśli podano <?użytkownika>, na kanale przez <?użytkownika> obrazek pojawił się wcześniej na serwerze.',
            '🤖',
        ),
        _Help.Command(
            ('magiel', 'magluj', 'mangle'),
            ('intensywność', '?tekst'),
            'Magluje <?tekst> lub, jeśli nie podano <?tekstu>, ostatnio wysłaną na kanale wiadomość w <intensywność> procentach.',
            '⌨️',
        ),
        _Help.Command('tableflip', (), '(╯°□°）╯︵ ┻━┻', '🤬',
            non_ai_usable=True),
        _Help.Command('unflip', (), '┬─┬ ノ( ゜-゜ノ)', '😞',
            non_ai_usable=True),
        _Help.Command('shrug', (), r'¯\_(ツ)_/¯', '🤷',
            non_ai_usable=True),
        _Help.Command(('lenny', 'lennyface'), (), '( ͡° ͜ʖ ͡°)', '😏',
            non_ai_usable=True),
        _Help.Command(('lenno', 'lennoface'), (), '( ͡ʘ ͜ʖ ͡ʘ)', '😼',
            non_ai_usable=True),
        _Help.Command(('dej', 'gib'), '?rzecz', '༼ つ ◕_◕ ༽つ <?rzecz>', '🤲',
            non_ai_usable=True),
        _Help.Command(
            ('nie', 'nope', 'no'),
            (),
            'Usuwa ostatnią wiadomość wysłaną przez bota na kanale jako rezultat użytej przez ciebie komendy.',
            '🗑',
        ),
        _Help.Command(
            ('warn', 'ostrzeż', 'ostrzez'),
            ('użytkownik Discorda', 'powód'),
            'Ostrzega <użytkownika Discorda>. '
            'Działa tylko dla członków serwera mających uprawnienia do wyrzucania innych.',
            '❗️',
            non_ai_usable=True
        ),
        _Help.Command(
            ('kick', 'wyrzuć', 'wyrzuc'),
            ('użytkownik Discorda', 'powód'),
            'Wyrzuca <użytkownika Discorda>. '
            'Działa tylko dla członków serwera mających uprawnienia do wyrzucania innych.',
            '👋',
            non_ai_usable=True
        ),
        _Help.Command(
            ('ban', 'zbanuj'),
            ('użytkownik Discorda', 'powód'),
            'Banuje <użytkownika Discorda>. Działa tylko dla członków serwera mających uprawnienia do banowania innych.',
            '🔨',
            non_ai_usable=True
        ),
        _Help.Command(
            ('przebacz', 'pardon'),
            ('użytkownik Discorda'),
            'Usuwa wszystkie ostrzeżenia <użytkownika Discorda> na serwerze. '
            'Działa tylko dla członków serwera mających uprawnienia administratora.',
            '🕊',
            non_ai_usable=True
        ),
        _Help.Command(
            'kartoteka',
            ('?użytkownik Discorda', '?typy zdarzeń'),
            'Sprawdza kartotekę <?użytkownika Discorda> pod kątem <?typów zdarzeń>. '
            'Jeśli nie podano <?użytkownika Discorda>, przyjmuje ciebie. '
            'Jeśli nie podano typu <?typów zdarzeń>, zwraca wszystkie zdarzenia.',
            '📂',
        ),
        _Help.Command(
            ('wyczyść', 'wyczysc'),
            '?liczba',
            'Usuwa <?liczbę> ostatnich wiadomości z kanału lub, jeśli nie podano <?liczby>, jedną ostatnią wiadomość '
            'z kanału na którym użyto komendy. Działa tylko dla członków serwera mających uprawnienia '
            'do zarządzania wiadomościami na kanale.',
            '🧹',
            non_ai_usable=True
        ),
        _Help.Command(
            ('prefiks', 'prefix'),
            '?podkomenda',
            'Komendy związane z własnymi serwerowymi prefiksami komend. '
            'Użyj bez <?podkomendy>, by dowiedzieć się więcej.',
            '🔧',
            non_ai_usable=True
        ),
        _Help.Command(
            'przetwarzanie-danych',
            (),
            'Narzędzia dotyczące przetwarzania Twoich danych przez Somsiada.',
            non_ai_usable=True
        ),
        _Help.Command(('komendadnia', 'cotd'), (), 'Pokazuje dzisiejszą komendę dnia.', '👀'),
        _Help.Command(('ping', 'pińg'), (), 'Pong!', '🏓',
            non_ai_usable=True),
        _Help.Command(('wersja', 'v'), (), 'Pokazuje działającą wersja bota.', '🍆'),
        _Help.Command(('informacje', 'info'), (), 'Pokazuje działającą wersja bota plus dodatkowe informacje.', 'ℹ️'),
    )
    DESCRIPTION = (
        'Somsiad jestem. Pomagam ludziom w różnych kwestiach. '
        'By skorzystać z mojej pomocy wystarczy wysłać komendę w miejscu, w którym będę mógł ją zobaczyć. '
        'Lista komend wraz z ich opisami znajduje się poniżej. '
        'Używając ich na serwerach pamiętaj o prefiksie (możesz zawsze sprawdzić go za pomocą '
        f'`{configuration["command_prefix"]}prefiks sprawdź`).\n'
        'W (nawiasach okrągłych) podane są aliasy komend.\n'
        'W <nawiasach ostrokątnych> podane są argumenty komend. Jeśli przed nazwą argumentu jest ?pytajnik, '
        'oznacza to, że jest to argument opcjonalny.'
    )

    def __init__(self, bot: Somsiad):
        self.bot = bot
        description = self.DESCRIPTION + f'\nBy dowiedzieć się o mnie więcej, wejdź na {self.bot.WEBSITE_URL}.'
        self.HELP = _Help(self.COMMANDS, '👋', 'Dobry!', description)

    async def cog_load(self):
        self.auto_command_of_the_day.start()

    def cog_unload(self):
        self.auto_command_of_the_day.cancel()

    @cooldown()
    @commands.command(aliases=['cotd', 'komendadnia'])
    async def command_of_the_day(self, ctx):
        await self.bot.send(ctx, embed=self.compose_command_of_the_day_embed())

    @tasks.loop(hours=24)
    async def auto_command_of_the_day(self):
        if self.bot.public_channel:
            await self.bot.public_channel.send(embed=self.compose_command_of_the_day_embed())

    @auto_command_of_the_day.before_loop
    async def before_command_of_the_day(self):
        now = dt.datetime.now().astimezone()
        next_iteration_moment = dt.datetime(now.year, now.month, now.day, *COTD_TIME).astimezone()
        if next_iteration_moment != now:
            if next_iteration_moment < now:
                next_iteration_moment += dt.timedelta(1)
            await discord.utils.sleep_until(next_iteration_moment)

    def compose_command_of_the_day_embed(self) -> discord.Embed:
        today = dt.date.today()
        today_number = (
            today.year * 10_000 + today.month * 100 + today.day
        )  # Eg. datetime 2024-07-30 is integer 20240730
        command_help_hash = int.from_bytes(
            hashlib.sha1(today_number.to_bytes(8, "big", signed=False)).digest(), "big", signed=False
        )
        command_help = self.COMMANDS[command_help_hash % len(self.COMMANDS)]
        today_name_days = NAME_DAYS[today.month][today.day]
        trade_sunday_info = ''
        if today.weekday() == 6:
            is_todays_sunday_trade = determine_nearest_trade_sunday_after_date(today) == today
            trade_sunday_info = " (handlowa)" if is_todays_sunday_trade else " (bez handlu)"
        embed = self.bot.generate_embed(
            command_help.emoji,
            f"Komenda dnia: {command_help.name}",
            f"{today.strftime(f'%A{trade_sunday_info}, %-d %B %Y').capitalize()}. Imieniny {join_using_and(today_name_days)}.",
        )
        embed.add_field(name=str(command_help), value=command_help.description, inline=False)
        return embed

    @cooldown()
    @commands.command(aliases=['help', 'pomocy', 'pomoc'])
    async def help_message(self, ctx):
        await self.bot.send(ctx, direct=True, embed=self.HELP.embeds)


async def setup(bot: Somsiad):
    await bot.add_cog(Help(bot))
