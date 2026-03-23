Jarvis Plugin Integration - Strategisches Protokoll
===================================================

Dieses Dokument definiert die technische Anbindung von Plugins und Tools
(MCP-Server) an das Jarvis-Ökosystem nach dem **RB-Protokoll**.

1. Plugin-Definition: Die Trinität der Tools
--------------------------------------------

Plugins werden in Jarvis in drei Kategorien unterteilt:

  **Kategorie**        **Beispiel**                **Ausführungsort**   **Sicherheits-Level**
  -------------------- --------------------------- -------------------- ---------------------------
  **System-Plugins**   SSD-Writer, Terminal, Git   jarvis-sandbox       Hoch (Hardware-Isolation)
  **Sovereign MCP**    Google Drive API, E-Mail    jarvis-gateway       Mittel (Privacy Masking)
  **Cloud-Plugins**    Perplexity Search, GitHub   jarvis-gateway       Niedrig (Hard-Filter)

2. Das MCP-Standard-Protokoll (Model Context Protocol)
------------------------------------------------------

Jarvis nutzt MCP als universellen Stecker. Jedes Plugin muss einen
MCP-Server bereitstellen.

**Workflow der Einbindung:**

1.  **Discovery:** Der User fügt einen MCP-Link im Chat hinzu.

2.  **Installation:** Das Plugin wird als Docker-Sub-Container im
    > isolierten Netzwerk registriert.

3.  **Permission-Check:** Jarvis prüft, welche Berechtigungen das Plugin
    > fordert (z.B. \"Read-only\" auf SSD 2).

4.  **Activation:** Ein Skill (aus dem Master-Katalog) erhält nun die
    > Erlaubnis, dieses Plugin aufzurufen.

3. Strategischer Prompt: \"The Tool Guardian\"
----------------------------------------------

Dies ist die MD-Anweisung für den Agenten, der Plugins verwaltet:

\#\#\# SYSTEM-PROMPT: Plugin Manager Agent

Du bist der Sentinel für die Tool-Schnittstellen.

Aufgabe: Überwache die Plugin-Aktivitäten.

Workflow:

1\. REQUEST-VALIDATION: Bevor ein Plugin einen Befehl ausführt, prüfe:
\'Entspricht dies der aktuellen Benutzeranfrage?\'

2\. DATA-LEAK-PREVENTION: Scanne die an Plugins gesendeten Daten nach
maskierten Werten (\[SECRET\_KEY\]). Diese dürfen niemals an Cloud-APIs
gesendet werden.

3\. LOGGING: Protokolliere jede Plugin-Interaktion im Trace-Log (Gesetz
1: Glass-Box).

Menschliche Hoheit: Plugin-Aktionen, die Daten LÖSCHEN oder KOSTEN
verursachen, benötigen ein Double-Check-Veto des Users.

4. UX-Integration: \"Toolbox Visibility\"
-----------------------------------------

Gemäß dem **Gesetz der Progressiven Offenlegung** werden aktive Plugins
in der UI wie folgt behandelt:

-   **Sidebar:** Ein kleines Icon zeigt, welche MCP-Server gerade
    > \"online\" sind.

-   **Chat:** Wenn ein Plugin arbeitet, erscheint eine dezente
    > Statusmeldung: *\"🛠️ Plugin \[GitHub\] lädt
    > Repository-Struktur\...\"*

-   **Inspect-Mode:** Per Klick auf das Tool-Icon sieht der User den
    > exakten JSON-Request/Response des Plugins (Forensische
    > Transparenz).

5. Security (Police-Prinzip)
----------------------------

Jedes neue Plugin wird beim ersten Start in einer \"Quarantäne-Instanz\"
der Sandbox ausgeführt. Erst wenn der \@security Agent bestätigt, dass
keine unbefugten Netzwerk-Calls abgesetzt werden, wird das Plugin für
das Hauptprojekt freigegeben.

*Status: Plugin-Integrations-Strategie finalisiert.* *Archiviert in:
Jarvis\_Development/strategy/*
