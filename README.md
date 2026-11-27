# ♟️ Python Schach & Engine-Testumgebung

Ein klassisches Schachspiel mit integrierter Schach-Engine und Live-Stellungsbewertung (Evaluation Bar), entwickelt in Python mit **Pygame** und **python-chess**.

## ✨ Features
* **Zwei Spielmodi:** Spiele lokal zu zweit gegen einen Freund oder tritt gegen den integrierten Schach-Bot an.
* **Live-Bewertung:** Integrierte Evaluation Bar zeigt dir in Echtzeit an, wer gerade im Vorteil ist.
* **Eigene Vektor-Grafiken:** Alle Schachfiguren werden direkt über Pygame gezeichnet – keine externen Bilddateien nötig.
* **Volle Regelvalidierung:** Unterstützt alle offiziellen Schachregeln (Rochade, En Passant, Bauernumwandlung, Schachmatt, Patt).

---

## 🎮 Steuerung

| Taste / Aktion | Funktion |
| :--- | :--- |
| **Linksklick** | Figur auswählen / Zielfeld wählen *(erneuter Klick hebt Auswahl auf)* |
| **Z** | Letzten Zug rückgängig machen *(Undo)* |
| **R** | Aktuelle Partie zurücksetzen *(Reset)* |
| **E** | Engine-Modus für Schwarz ein-/ausschalten |
| **ESC** | Zurück zur Startseite / Spielmodus-Auswahl |

---

## 📥 Download & Start (Windows)

Für Windows steht eine fertige `.exe`-Datei bereit – du musst kein Python installieren:

1. Gehe rechts auf **[Releases](../../releases)** und lade die aktuelle `.exe`-Datei herunter.
2. Starte die Datei per Doppelklick.

> **Hinweis zu Windows SmartScreen:** Da das Programm nicht kostenpflichtig digital signiert ist, erscheint beim ersten Start möglicherweise die Meldung *„Der Computer wurde durch Windows geschützt“*. Klicke in diesem Fenster einfach auf **Weitere Informationen** und anschließend auf **Trotzdem ausführen**.

---

## 🛠️ Selbst ausführen (aus dem Quellcode)

Falls du das Spiel direkt über Python starten oder auf macOS/Linux nutzen möchtest:

1. **Repository klonen:**
   ```bash
   git clone [https://github.com/Dawid2504/Chess.git](https://github.com/Dawid2504/Chess.git)
   cd Chess
