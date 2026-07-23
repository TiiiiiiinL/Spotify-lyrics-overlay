# 🎤 Spotify Lyrics Overlay

En flytande, alltid-överst **undertext för Spotify** — som i en film. Texten
ligger längst fram ovanpå alla fönster, byts rad-för-rad i takt med låten, och
går att dra dit du vill med musen.

![stil](https://img.shields.io/badge/stil-filmundertext-blue) källa: **lrclib.net** (gratis, synkade texter)

---

## ⚠️ Viktigt: kör i Windows, inte i WSL

Programmet ska rita ovanpå dina vanliga Windows-fönster. Därför måste det köras
med **Windows-Python**, inte i WSL/Linux-terminalen. Stegen nedan är för Windows.

> Filerna ligger i WSL. Öppna dem i Windows genom att klistra in detta i
> Utforskarens adressfält: `\\wsl.localhost\Ubuntu\home\<user>\spotify-lyrics-overlay`
> (byt `Ubuntu` mot ditt Linux-namn om det heter något annat). Kopiera gärna
> mappen till t.ex. `Dokument` så blir det enklare.

---

## 1. Installera Python (om du inte har det)

Ladda ner från <https://www.python.org/downloads/> och **kryssa i
"Add Python to PATH"** under installationen.

## 2. Installera de delar programmet behöver

Öppna **Kommandotolken** (sök "cmd" i Start), gå till mappen och kör:

```cmd
cd "C:\sökväg\till\spotify-lyrics-overlay"
pip install -r requirements.txt
```

## 3. Skapa en gratis Spotify-app (för att läsa vad som spelas)

1. Gå till <https://developer.spotify.com/dashboard> och logga in.
2. Klicka **Create app**. Namn/beskrivning spelar ingen roll.
3. I fältet **Redirect URI**, skriv exakt:
   `http://127.0.0.1:8888/callback` och klicka **Add**, sedan **Save**.
4. Öppna appen → **Settings**. Kopiera **Client ID** och **Client secret**.

## 4. Lägg in dina nycklar

Kopiera `config.example.py` → `config.py` och klistra in dina värden:

```python
CLIENT_ID = "ditt-client-id"
CLIENT_SECRET = "ditt-client-secret"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
```

> 🔒 **Din `config.py` är privat.** Den ligger i `.gitignore` och laddas
> aldrig upp till GitHub, eftersom den innehåller dina egna Spotify-nycklar.
> Filen `.spotify_cache` (din inloggning) är också ignorerad. Ladda alltid
> upp `config.example.py` – aldrig `config.py`.

## 5. Starta!

Dubbelklicka på **`run.bat`**, eller kör i Kommandotolken:

```cmd
python main.py
```

Första gången öppnas en webbläsare där du loggar in på Spotify och godkänner.
Sedan kommer du tillbaka automatiskt — det behövs bara en gång.

Spela en låt i Spotify, så dyker undertexten upp! 🎶

---

## Använda overlayn

| Vad | Hur |
|-----|-----|
| **Flytta** | Dra med vänster musknapp |
| **Öppna inställningar** | Klicka på ikonen i aktivitetsfältet, eller högerklicka på texten → Inställningar |
| **Större / mindre text** | Inställningar, eller `+` / `–` |
| **Lås position** | Högerklicka på texten → Lås position |
| **Avsluta** | Aktivitetsfält-ikon → Avsluta, högerklick → Avsluta, eller `Esc` |

## Inställningar

Öppna inställningsfönstret via **aktivitetsfält-ikonen** (nere vid klockan) eller
**högerklick på texten → Inställningar**. Allt ändras *live*:

- **Textstorlek** och **textfärg / konturfärg**
- **Bakgrund** på/av och hur **genomskinlig** den mörka plattan är
- **Visa kommande rad** på/av och **radavstånd**
- **Synk-justering** — skjut texten några tiondels sekunder fram/bak om den
  ligger före/efter låten (`+` = texten byts tidigare)

Alla inställningar och fönstrets position **sparas automatiskt** och finns kvar
till nästa gång. De ligger i `settings.json` i appens datamapp
(`…\AppData\Local\SpotifyLyricsOverlay`).

## Aktivitetsfältet

Appen lägger en liten ikon nere vid klockan. **Klicka** på den för att öppna
inställningar, eller **högerklicka** för menyn (Inställningar / Avsluta). Appen
lever kvar där även om du stänger inställningsfönstret.

## Bygga en app-fil (.exe)

Vill du slippa cmd/Python helt och få en dubbelklickbar app?

1. Dubbelklicka på **`build.bat`** (eller kör den i cmd).
2. Vänta medan den bygger — det tar någon minut.
3. Din färdiga app ligger sedan i mappen **`dist\SpotifyLyricsOverlay.exe`**.

Den filen innehåller allt (kod + Python + byggdelar), så den går att flytta vart
du vill och starta med ett dubbelklick. Inloggningen och inställningarna sparas i
`AppData`, så de finns kvar mellan starter.

> 🔒 Obs: dina Spotify-nycklar bakas in i `.exe`-filen. Det är okej för personligt
> bruk, men dela inte filen offentligt.
>
> 🐞 Eftersom `.exe`:n körs utan konsol skrivs statusmeddelanden till
> `…\AppData\Local\SpotifyLyricsOverlay\log.txt` — kika där om något strular.

---

## Vanliga problem

- **"Ingen synkad text hittades"** — låten saknas på lrclib.net, eller har bara
  oickad text. Vanligt med väldigt nya eller obskyra låtar.
- **Inget händer** — kollar Spotify verkligen att en låt *spelas* (inte pausad)?
  Web API:t rapporterar bara aktiv uppspelning.
- **Texten ligger lite efter/före** — overlayn synkar om var ~2 sek mot Spotify.
  Små avvikelser kan bero på Spotifys egen fördröjning.
- **Inloggningsfönstret kommer inte tillbaka** — kontrollera att Redirect URI i
  Spotify-appen är *exakt* `http://127.0.0.1:8888/callback`.

---

## Hur det fungerar (kort)

```
Spotify Web API  ──►  vad spelas + position (var 2:a sek)
lrclib.net       ──►  tidssynkad text (LRC) för låten
main.py          ──►  räknar ut vilken rad just nu (interpolerar mellan polls)
overlay.py       ──►  ritar raden, ramlöst/genomskinligt/alltid överst
```
