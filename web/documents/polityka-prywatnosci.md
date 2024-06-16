## Czego dotyczy ten dokument?

Polityka prywatności, którą właśnie czytasz, wyjaśnia sposób przetwarzania danych użytkowników bota discordowego [Somsiad](https://somsiad.net) (zwanego dalej **Botem**) przez operatora usługi (zwanego dalej **Operatorem**).

## Kto zalicza się do użytkowników Bota?

Jesteś użytkownikiem Bota jeśli należysz do jakiegokolwiek kanału na platformie Discord, do którego należy również Bot.
Ze względu na funkcje Bota dotyczące statystyk aktywności, zaliczasz się do użytkowników, nawet jeśli nie skorzystałeś jeszcze osobiście z żadnej z jego komend.

## Jakie dane i dlaczego gromadzi Operator?

2. W ramach komendy _stat_ dla każdej wysłanej przez Ciebie na czacie wiadomości przechowywane są:

    - twoje ID użytkownika Discorda
    - ID wiadomości
    - ID kanału
    - ID serwera
    - liczba słów w wiadomości
    - liczba znaków w wiadomości
    - data i czas wysłania

    Powyższe dane pozwalają na generowanie raportów aktywności w obrębie serwera poprzez wywołanie komendy _stat_.
    W tym procesie treść wiadomości nigdy nie zostaje zapisana poza Discordem, gdyż do analizy statystycznej potrzebne są tylko metadane wymienione wyżej.

1. W ramach komendy _było_ dla każdego wysłanego przez Ciebie na czacie obrazka przechowywane są:

    - twoje ID użytkownika Discorda
    - ID załącznika zawierającego obraz
    - ID wiadomości
    - ID kanału
    - ID serwera
    - hash percepcyjny obrazu
    - tekst znajdujący się na obrazku
    - data i czas wysłania

    Powyższe dane pozwalają na wizualne wyszukiwanie obrazów w obrębie serwera poprzez wywołanie komendy _było_.
    Obliczenia dające w rezultacie hash percepcyjny obrazu są nieodwracalne, więc żaden obraz nie zostaje zapisany poza Discordem.

1. Jeśli skorzystałeś z komendy _urodziny zapamiętaj_, przechowywane jest powiązanie Twojego ID użytkownika Discorda z datą urodzin.

    Twoja data urodzin jest domyślnie publiczna – tj. dostępna na żądanie dla wszystkich użytkowników – tylko na serwerze na którym użyłeś komendy _urodziny zapamiętaj_. Wszędzie indziej jest ona prywatna – tj. nikt nie może jej zobaczyć. Możesz w dowolnym momencie zmienić widoczność swojej daty urodzin odrębnie dla każdego serwera przy użyciu komend _urodziny upublicznij_/_urodziny utajnij_.

    Możesz także w dowolnym momencie całkowicie usunąć swoją datę urodzin z systemu Somsiada przy użyciu komendy _urodziny zapomnij_.

## Jak przechowywane są powyższe dane?

Dane przetwarzane przechowywane są w wewnętrznej bazie danych Bota. Operator nie udostępnia danych żadnej stronie trzeciej.

## Jak mogę zażądać usunięcia swoich danych?

Masz prawo do likwidacji wszystkich dotyczących Ciebie danych przechowywanych przez Operatora.

Najprostszym rozwiązaniem jest użycie komendy _przetwarzanie-danych wypisz_, która usunie wszystkie związane z tobą dane z bazy danych Bota i zapobiegnie ich przetwarzaniu w przyszłości. Swoją decyzję odnośnie przetwarzania danych w przyszłości możesz w każdej chwili cofnąć przy użyciu komendy _przetwarzanie-danych zapisz_, lecz raz usuniętych danych nie da się w żaden sposób przywrócić.

Poza tym możesz zgłosić takie życzenie za pośrednictwem [oficjalnego serwera discordowego Somsiad Labs](http://discord.gg/xRCpDs7). Życzenie zostanie zrealizowane w ciągu 7 dni, o czym zostaniesz poinformowany.

## Co jeśli mam dalsze pytania?

Odpowiedzi na wszelkie pytania związane z przetwarzaniem danych przez Bota uzyskasz za pośrednictwem [oficjalnego serwera discordowego Somsiad Labs](http://discord.gg/xRCpDs7).
