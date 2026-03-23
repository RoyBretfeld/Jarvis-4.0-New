Jarvis RAG Privacy Filter - Strategisches Protokoll
===================================================

Dieses Dokument definiert die Logik für den **Sovereign Privacy Layer**.
Er fungiert als \"Zollstation\" zwischen deinem lokalen RAG (Wissen aus
Drive) und der externen Reasoning-Cloud (Nemotron 3 Super).

1. Die Mission (Police-Prinzip)
-------------------------------

Keine sensiblen Hard-Facts dürfen die lokale Umgebung im Klartext
verlassen. Der Filter-Agent stellt sicher, dass die \"Intelligenz\" der
Cloud genutzt werden kann, ohne die \"Geheimnisse\" zu preisgeben.

2. Der \"Privacy Filter\" Prompt
--------------------------------

Dies ist die MD-Anweisung für das Modul, das den Kontext bereinigt:

\#\#\# SYSTEM-PROMPT: Privacy Filter Agent

Du bist der Sentinel für Datensouveränität. Deine Aufgabe ist das
\"Redacting\" von Kontext-Daten.

Workflow:

1\. SCAN: Durchsuche den vom RAG gelieferten Text nach:

\- API-Keys, Passwörtern, Tokens (Entropie-Check).

\- IP-Adressen und internen Pfaden (z.B. C:/Users/Roy/\...).

\- Namen von Personen oder spezifischen Firmen-IDs.

2\. MASKING: Ersetze Funde durch standardisierte Platzhalter:

\- \[SECRET\_KEY\_1\], \[INTERNAL\_IP\], \[USER\_PATH\], \[PII\_NAME\].

3\. MAPPING: Erstelle lokal eine flüchtige \'substitution.json\', damit
die Rückantwort der Cloud wieder \"entmaskiert\" werden kann.

Gesetz der Transparenz: Gib im Log-Fenster von Jarvis aus: \"🛡️ 3
Secrets und 1 IP maskiert.\"

3. Re-Substitution (Der Rückweg)
--------------------------------

Sobald Nemotron den Code oder die Antwort liefert, greift die lokale
Logik:

-   Jarvis prüft die Antwort auf die zuvor vergebenen Platzhalter.

-   Anhand der substitution.json werden die echten Werte (z.B. deine
    > lokale IP) wieder in den Code eingesetzt, bevor er im
    > Monaco-Editor erscheint.

-   **Wichtig:** Dieser Schritt passiert ausschließlich lokal auf deinem
    > Rechner.

4. Sicherheits-Kategorien (Blacklist)
-------------------------------------

Folgende Muster werden automatisch blockiert oder maskiert: \| Typ \|
Muster / Beispiel \| Aktion \| \| :\-\-- \| :\-\-- \| :\-\-- \| \|
**Credentials** \| password:, api\_key:, .env Inhalt \| Hard-Masking \|
\| **Infrastruktur** \| 192.168.x.x, ssh -i \... \| Hard-Masking \| \|
**Pfade** \| /home/user/documents/\... \| Relativierung \|

5. Architekten-Vorgabe für Fehlermeldungen
------------------------------------------

Falls die Cloud einen Fehler meldet, der ein maskiertes Element
betrifft:

-   Der Filter-Agent fängt die Fehlermeldung ab.

-   Er \"übersetzt\" den Fehler für dich (z.B. \"Die Verbindung zu
    > \[INTERNAL\_IP\] ist fehlgeschlagen\").

-   Damit bleibt die **Glass-Box** gewahrt, ohne Daten zu leaken.

*Status: Privacy-Filter-Strategie finalisiert.* *Erstellt durch: The
Architekt*
